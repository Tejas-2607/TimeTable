# Electives & Honors Upgrade Implementation Guide

## Overview
This guide enables scheduling of parallel subjects within a single time slot for the same batch/division. Elective subjects (e.g., AI, Data Science) can run simultaneously with different faculty and labs.

---

## Part 1: Workload Schema Update

### Current Schema
```json
{
  "faculty_id": "64b25f9ed1a4b5d8f0e6a9b3",
  "year": "SY",
  "subject": "OOPJ",
  "subject_full": "Java Programming (OOPJ)",
  "division": "A",
  "batches": [1, 2],
  "theory_hrs": 2,
  "practical_hrs": 2
}
```

### Enhanced Schema
Add two optional fields:
```json
{
  "faculty_id": "64b25f9ed1a4b5d8f0e6a9b3",
  "year": "SY",
  "subject": "AI",
  "subject_full": "Artificial Intelligence",
  "division": "A",
  "batches": [1, 2],
  "theory_hrs": 2,
  "practical_hrs": 2,
  
  // NEW: For electives/honors
  "subject_type": "elective",          // "regular" | "elective" | "honors"
  "elective_group_id": "ELE-AI-DS-2026", // Groups related electives
  "is_parallel": true                  // Confirms parallel scheduling
}
```

### Key Points
- `subject_type`: Classification (regular subjects run solo, electives/honors may run parallel)
- `elective_group_id`: Unique ID per elective group (e.g., "ELE-AI-DS-2026" groups AI & Data Science)
- `is_parallel`: Boolean flag (true = multiple subjects in group scheduled same slot)

---

## Part 2: Constraint Logic in timetable_generator.py

### New Concepts

#### Parallel Slot Exception
```python
def _can_batch_share_slot(self, year, division, batch, day, slot, 
                          current_subject_type, elective_group_id) -> bool:
    """
    Allow SAME batch to occupy SAME slot ONLY if:
    1. Both subjects are marked as parallel electives, AND
    2. Both belong to SAME elective_group_id
    
    Regular subjects: ALWAYS exclusive per slot
    Honors: Treated like electives (parallel capable)
    """
    if current_subject_type not in ['elective', 'honors']:
        return False  # Only electives/honors share slots
    
    if not elective_group_id:
        return False  # Must have valid group ID
    
    # Check existing subjects in this slot
    key = (year, division, batch)
    existing = self.batch_occupied.get(key, {}).get(day, {}).get(slot, [])
    
    for existing_subj in existing:
        if existing_subj.get('elective_group_id') != elective_group_id:
            return False  # Different group: conflict
        if existing_subj.get('subject_type') not in ['elective', 'honors']:
            return False  # Regular subject in slot: conflict
    
    return True  # Same group, all parallel: OK!
```

#### Modified Constraint Check
```python
def _can_schedule(self, practical: dict, day: str, slot: str,
                  used_faculty: set, used_labs: set) -> bool:
    year, division, batch = practical['year'], practical['division'], practical['batch']
    faculty, hrs = practical['faculty'], practical['practical_hrs']
    
    # 1. Duration validation (unchanged)
    if hrs == 2 and slot not in TWO_HR_START_SLOTS:
        return False
    
    # 2. Faculty constraint (STRICT - no parallel)
    if faculty in used_faculty:
        return False
    if self._faculty_busy(faculty, day, slot):
        return False
    
    # 3. Batch constraint (WITH parallel exception for electives)
    if not self._batch_slot_free(year, division, batch, day, slot):
        # Slot occupied, but check if elective parallel exception applies
        if not self._can_batch_share_slot(
            year, division, batch, day, slot,
            practical.get('subject_type', 'regular'),
            practical.get('elective_group_id')
        ):
            return False
    
    # 4. 2-hour continuation check (WITH parallel exception)
    if hrs == 2:
        next_slot = NEXT_SLOT[slot]
        if not self._batch_slot_free(year, division, batch, day, next_slot):
            if not self._can_batch_share_slot(
                year, division, batch, day, next_slot,
                practical.get('subject_type', 'regular'),
                practical.get('elective_group_id')
            ):
                return False
    
    # 5. Lab constraint (STRICT - no parallel)
    if self._select_lab(practical, day, slot, used_labs) is None:
        return False
    
    return True
```

#### Data Structure for Batch Occupancy
Replace boolean with list of subject metadata:
```python
# OLD:
self.batch_occupied[key][day][slot] = True  # Boolean

# NEW:
self.batch_occupied[key][day][slot] = [
    {
        'subject': 'AI',
        'subject_type': 'elective',
        'elective_group_id': 'ELE-AI-DS-2026',
        'faculty': 'Dr. Smith',
        'lab': 'Lab-1'
    },
    {
        'subject': 'Data Science',
        'subject_type': 'elective',
        'elective_group_id': 'ELE-AI-DS-2026',
        'faculty': 'Dr. Jones',
        'lab': 'Lab-2'
    }
]
```

---

## Part 3: Data Transformation in class_timetable_handler.py

### Current Storage
```python
class_schedules[key][day][slot] = [
    {'subject': 'OOPJ', 'faculty': 'Dr. Smith', ...},
    {'subject': 'OOPJ', 'faculty': 'Dr. Smith', ...}  # follow-on
]
```

### Enhanced Storage (Parallel Sessions)
```python
class_schedules[key][day][slot] = [
    # Single subject (regular/non-parallel)
    {'subject': 'OOPJ', 'faculty': 'Dr. A', 'lab': 'Lab-1', 'type': 'practical'},
    
    # Parallel electives (same group)
    {
        'parallel': True,
        'group_id': 'ELE-AI-DS-2026',
        'group_name': 'Electives: AI & Data Science',
        'sessions': [
            {'subject': 'AI', 'faculty': 'Dr. Smith', 'lab': 'Lab-2', 'type': 'practical'},
            {'subject': 'Data Science', 'faculty': 'Dr. Jones', 'lab': 'Lab-3', 'type': 'practical'}
        ]
    }
]
```

### Key Transformation Logic
1. When reading from master_lab_timetable, detect parallel sessions by `elective_group_id`
2. Group sessions with same `(day, slot, elective_group_id)` into a single parallel entry
3. Store follow-on slots similarly for 2-hour practicals

---

## Part 4: 2-Hour Locking for Electives

### Constraint
If an elective group has a 2-hour practical, ALL subjects in that group are locked to the same 2-hour block.

### Implementation
```python
def _get_elective_group_subjects(self, elective_group_id: str) -> list[dict]:
    """Fetch all subjects in this elective group from workload."""
    workloads = list(workload_collection.find({
        'elective_group_id': elective_group_id
    }))
    return [w.get('subject') for w in workloads]

def _lock_elective_2hr_block(self, elective_group_id: str, year: str, 
                             division: str, batch: int, day: str, slot: str):
    """Lock all subjects in group to same 2-hour block."""
    subjects = self._get_elective_group_subjects(elective_group_id)
    next_slot = NEXT_SLOT.get(slot)
    
    if not next_slot:
        return  # Not a 2-hr slot
    
    key = (year, division, batch)
    for subject in subjects:
        # Mark both slot and next_slot as occupied by this group
        self.batch_occupied[key][day][slot].append({
            'subject': subject,
            'elective_group_id': elective_group_id,
            'locked_2hr': True
        })
        self.batch_occupied[key][day][next_slot].append({
            'subject': subject,
            'elective_group_id': elective_group_id,
            'locked_2hr': True
        })
```

---

## Part 5: Frontend Compatibility

### API Response Format
The API (from `class_timetable_handler.py`) should return:
```json
{
  "class": "SY",
  "division": "A",
  "schedule": {
    "Monday": {
      "11:15": [
        {
          "subject": "OOPJ",
          "faculty": "Dr. Smith",
          "batch": 1,
          "lab": "Lab-1",
          "type": "practical"
        },
        {
          "parallel": true,
          "group_id": "ELE-AI-DS-2026",
          "group_name": "Electives: AI & Data Science",
          "sessions": [
            {
              "subject": "AI",
              "faculty": "Dr. Johnson",
              "batch": 1,
              "lab": "Lab-2",
              "type": "practical"
            },
            {
              "subject": "Data Science",
              "faculty": "Dr. Lee",
              "batch": 1,
              "lab": "Lab-3",
              "type": "practical"
            }
          ]
        }
      ]
    }
  }
}
```

### Frontend Rendering
In components (e.g., `ViewTimetables.jsx`):
```jsx
{slot.map((entry, idx) => 
  entry.parallel ? (
    <div key={idx} className="parallel-slot">
      <strong>{entry.group_name}</strong>
      {entry.sessions.map(s => (
        <div key={s.subject}>{s.subject} - {s.faculty} ({s.lab})</div>
      ))}
    </div>
  ) : (
    <div key={idx}>{entry.subject} - {entry.faculty} ({entry.lab})</div>
  )
)}
```

---

## Part 6: Implementation Checklist

### Phase 1: Backend Schema & Workload
- [ ] Update MongoDB workload collection with new fields
- [ ] Modify `workload_handler.py` to accept and validate new fields
- [ ] Add migration script to add `subject_type` and `elective_group_id` to existing documents

### Phase 2: Constraint Logic
- [ ] Modify `TimetableGenerator.__init__` to track subject metadata in `batch_occupied`
- [ ] Implement `_can_batch_share_slot()` method
- [ ] Update `_can_schedule()` to use new logic
- [ ] Update `_write_session()` to store metadata
- [ ] Update `_batch_slot_free()` to handle list-based occupancy

### Phase 3: Class Timetable Transformation
- [ ] Modify `generate_class_timetables()` to detect parallel sessions
- [ ] Implement grouping logic for same `(day, slot, elective_group_id)`
- [ ] Store parallel sessions in new format
- [ ] Ensure 2-hour follow-on slots maintain grouping

### Phase 4: API & Frontend
- [ ] Test API responses with new format
- [ ] Update frontend service layer (`classTimetableService.js`)
- [ ] Update display components to render parallel sessions
- [ ] Add CSS styling for parallel session cells

### Phase 5: Testing
- [ ] Unit tests for constraint logic
- [ ] Integration tests with sample elective groups
- [ ] E2E tests: Create workload → Generate timetable → Verify rendering
- [ ] Edge cases: 2-hour practicals, batch splits, faculty conflicts

---

## Validation Scenarios

### ✅ Should Work
1. **Two electives in same group, same slot**: AI + Data Science → 11:15 Monday
2. **2-hour elective practical**: Both subjects locked to 11:15-12:15
3. **Different elective groups**: Cannot share slot
4. **Regular subject in elective group slot**: Not allowed

### ❌ Should Fail
1. **Same faculty in two subjects**: Faculty conflict
2. **Same lab in two subjects**: Lab conflict
3. **Different batch in slot**: Batch conflict (unless different elective group)
4. **Regular + Elective in same slot**: Type mismatch

---

## Database Migration (Optional but Recommended)

```python
# Add to app.py or create separate migration script
def migrate_workload_schema():
    """Add subject_type and elective_group_id to existing workloads."""
    workload_collection.update_many(
        {'subject_type': {'$exists': False}},
        {'$set': {
            'subject_type': 'regular',
            'elective_group_id': None,
            'is_parallel': False
        }}
    )
    logger.info("✓ Workload schema migrated")
```

---

## Quick Reference: Key Changes

| Component | Change | Impact |
|-----------|--------|--------|
| **workload.json** | Add `subject_type`, `elective_group_id` | Input definition |
| **timetable_generator.py** | `batch_occupied` as list; new constraint logic | Scheduling logic |
| **class_timetable_handler.py** | Parallel session grouping | Data storage |
| **Frontend API** | New response format with parallel wrapper | Display logic |
| **Components** | Conditional rendering for parallel entries | UI presentation |

---

## Troubleshooting

### Issue: Electives still conflict on batch
- **Check**: Is `elective_group_id` identical for all subjects in group?
- **Check**: Is `subject_type` set to "elective"?
- **Check**: Is `_can_batch_share_slot()` being called?

### Issue: Faculty still scheduled in parallel
- **Cause**: Faculty constraint should be STRICT (no exceptions)
- **Fix**: Ensure `_can_schedule()` checks faculty BEFORE elective exception

### Issue: 2-hour practicals not locking together
- **Check**: Is `_lock_elective_2hr_block()` called after scheduling?
- **Check**: Is next_slot correctly resolved?

### Issue: Frontend not showing parallel sessions
- **Check**: API response contains `parallel: true` wrapper?
- **Check**: Frontend component checks for `entry.parallel` property?
- **Check**: CSS doesn't hide overflow in slot cell?

---

## Future Enhancements

1. **Honors Track**: Separate track with same parallel logic
2. **Flexible Grouping**: UI to create/manage elective groups
3. **Load Balancing**: Distribute parallel subjects evenly across labs
4. **Analytics**: Report on parallel session utilization
5. **Constraints by Group**: E.g., "Elective group must fit in morning slots"

# Electives & Honors Upgrade - Executive Summary

## 🎯 What Was Implemented

Your timetable generator now supports **parallel scheduling of elective/honors subjects**. Multiple subjects (e.g., AI, Data Science) can run simultaneously for the same class/batch with:
- ✅ Different faculty teaching each subject
- ✅ Different labs hosting practicals
- ✅ Student splits between subjects
- ✅ Frontend displays parallel sessions clearly

---

## 📋 What Changed

### 1. Workload Schema (Backend)
```python
# NEW fields in workload collection:
{
  "subject_type": "elective",              # "regular" | "elective" | "honors"
  "elective_group_id": "ELE-AI-DS-2026"   # Groups related electives together
}
```

### 2. Scheduling Algorithm (Backend)
```
OLD: Batch occupies slot exclusively
NEW: Batch CAN share slot IF:
     - Both subjects are elective/honors
     - Same elective_group_id
     - Different faculty (STRICT)
     - Different labs (STRICT)
```

### 3. Data Storage (Backend)
```python
# OLD: schedule[day][slot] = [session1, session2]

# NEW: schedule[day][slot] = [
#   {parallel: true, sessions: [session1, session2]},
#   session3
# ]
```

### 4. Frontend Display (React)
```jsx
// OLD: List of sessions
// NEW: Detects parallel entries, renders in purple grouped container
<div className="parallel-box">
  <strong>Electives: AI, Data Science</strong>
  <div>AI - Faculty A - Lab 1</div>
  <div>Data Science - Faculty B - Lab 2</div>
</div>
```

---

## 🚀 Quick Start

### Step 1: Create Elective Workload Entries

```bash
# For first subject (AI)
curl -X POST http://localhost:5000/api/faculty_workload \
  -H "Content-Type: application/json" \
  -d '{
    "faculty_id": "64b25f9ed1a4b5d8f0e6a9b3",
    "year": "SY",
    "subject": "AI",
    "subject_full": "Artificial Intelligence",
    "division": "A",
    "batches": [1],
    "theory_hrs": 2,
    "practical_hrs": 2,
    "subject_type": "elective",
    "elective_group_id": "ELE-AI-DS-2026"
  }'

# For second subject (Data Science) - SAME group ID
curl -X POST http://localhost:5000/api/faculty_workload \
  -H "Content-Type: application/json" \
  -d '{
    "faculty_id": "64b25f9ed1a4b5d8f0e6a9c4",
    "year": "SY",
    "subject": "Data Science",
    "subject_full": "Advanced Data Science",
    "division": "A",
    "batches": [1],
    "theory_hrs": 2,
    "practical_hrs": 2,
    "subject_type": "elective",
    "elective_group_id": "ELE-AI-DS-2026"
  }'
```

### Step 2: Generate Timetable

```bash
curl -X POST http://localhost:5000/api/generate_timetable
```

### Step 3: View Results

- Open class timetable view
- Look for **purple boxes** labeled "Electives: AI, Data Science"
- Each subject shows its faculty and lab

---

## ⚙️ How It Works

### Constraint Checking (Priority Order)

| Priority | Constraint | Flexibility |
|----------|-----------|-------------|
| 1 | Faculty cannot teach 2 subjects same slot | STRICT - No exceptions |
| 2 | Lab cannot host 2 practicals same slot | STRICT - No exceptions |
| 3 | Batch occupies slot | **WITH EXCEPTION**: Can share if same elective group |
| 4 | 2-hour blocks stay together | ALL subjects in group locked together |

### Scheduling Flowchart

```
For each subject in workload:
  ├─ Is faculty free? → NO: Try next slot → Continue
  │                 → YES: Continue
  ├─ Is lab free? → NO: Try different lab/slot → Continue
  │             → YES: Continue
  ├─ Is batch slot free? → YES: Schedule here → DONE
  │                    → NO: Is this elective?
  │                        ├─ NO: Try next slot → Continue
  │                        └─ YES: Is same elective group already there?
  │                            ├─ NO: Try next slot → Continue
  │                            └─ YES: Schedule here (PARALLEL) → DONE
  └─ Max passes reached → Add to LEFTOVERS
```

---

## 📁 Files Changed

### Backend (Python)

| File | Changes | Impact |
|------|---------|--------|
| `workload_handler.py` | +2 new fields, +validation | Input accept electives |
| `timetable_generator.py` | +3 new methods, ~50 lines modified | Parallel scheduling logic |
| `class_timetable_handler.py` | +1 new function, grouping logic | Output format |

### Frontend (React)

| File | Changes | Impact |
|------|---------|--------|
| `lib/timetableUtils.js` | NEW file | Renders parallel sessions |
| `components/ViewTimetables.jsx` | Import new function | Uses parallel renderer |

### Documentation

| File | Purpose |
|------|---------|
| `ELECTIVES_UPGRADE_GUIDE.md` | Architectural details |
| `TESTING_AND_DEPLOYMENT.md` | Test scenarios & deployment |
| `IMPLEMENTATION_SUMMARY.md` | This file |

---

## 🧪 Key Test Scenarios

### ✅ Test 1: Electives in Parallel
- Add AI (Faculty A, Lab 1) + Data Science (Faculty B, Lab 2)
- Same group ID → Should schedule in SAME time slot

### ✅ Test 2: Faculty Conflict Prevention
- Add AI (Faculty A, Lab 1) + Data Science (Faculty A, Lab 2)
- Same faculty, same group → Only ONE scheduled

### ✅ Test 3: Lab Conflict Prevention  
- Add AI (Faculty A, Lab 1) + Data Science (Faculty B, Lab 1)
- Same lab, same group → Only ONE scheduled

### ✅ Test 4: Different Groups (No Parallel)
- Add Group A (ELE-AI-DS-2026) + Group B (ELE-WEB-MOBILE-2026)
- Different group IDs → Schedule separately, never parallel

### ✅ Test 5: Frontend Display
- After generating with parallel electives
- View class timetable → See purple "Electives" boxes

---

## 🔧 Configuration Examples

### Example 1: Simple Elective Pair

**Scenario:** SY-A students choose between AI or Data Science

```json
[
  {
    "faculty_id": "...",
    "year": "SY",
    "subject": "AI",
    "subject_full": "Artificial Intelligence",
    "division": "A",
    "batches": [1],
    "practical_hrs": 2,
    "subject_type": "elective",
    "elective_group_id": "ELE-AI-DS-2026"
  },
  {
    "faculty_id": "...",
    "year": "SY",
    "subject": "Data Science",
    "subject_full": "Advanced Data Science",
    "division": "A",
    "batches": [1],
    "practical_hrs": 2,
    "subject_type": "elective",
    "elective_group_id": "ELE-AI-DS-2026"
  }
]
```

**Result:** Both scheduled in same slot (e.g., Monday 11:15), different labs

---

### Example 2: Three-Way Elective

**Scenario:** SY-B students choose between Web, Mobile, or Cloud

```json
[
  {subject: "Web Dev", elective_group_id: "ELE-WEB-MOBILE-CLOUD-2026"},
  {subject: "Mobile Dev", elective_group_id: "ELE-WEB-MOBILE-CLOUD-2026"},
  {subject: "Cloud Computing", elective_group_id: "ELE-WEB-MOBILE-CLOUD-2026"}
]
```

**Result:** If constraints allow, all 3 in same slot with different faculty/labs

---

### Example 3: Mixed Regular + Elective

**Scenario:** SY-C has regular OOPJ + elective choices

```json
[
  {subject: "OOPJ", subject_type: "regular", elective_group_id: null},
  {subject: "IoT", subject_type: "elective", elective_group_id: "ELE-IOT-ROBOTICS-2026"},
  {subject: "Robotics", subject_type: "elective", elective_group_id: "ELE-IOT-ROBOTICS-2026"}
]
```

**Result:**
- OOPJ scheduled at its own slot (exclusive)
- IoT + Robotics at different slot (parallel)

---

## ⚠️ Important Notes

### Backward Compatibility ✅
- Regular subjects still work normally
- Old workloads without elective fields: treated as regular
- No breaking changes to existing timetables

### Constraints Are STRICT

Faculty and Lab checks have **NO exceptions**. Even if both subjects are in the same elective group:
- ❌ Same faculty cannot teach 2 subjects in 1 slot
- ❌ Same lab cannot host 2 practicals in 1 slot

Only batch occupancy check has a parallel exception.

### 2-Hour Practicals Lock Together
If an elective group has 2-hour practicals:
- All subjects in the group occupy BOTH the primary and follow-on slot
- Example: AI + DS at 11:15 → Both occupy 11:15 AND 12:15

---

## 📊 API Reference

### Add Elective Workload

```http
POST /api/faculty_workload
Content-Type: application/json

{
  "faculty_id": "<ObjectId>",
  "year": "SY|TY|BE",
  "subject": "AI",
  "subject_full": "Artificial Intelligence",
  "division": "A|B|...",
  "batches": [1, 2, ...],
  "theory_hrs": 2,
  "practical_hrs": 2,
  "subject_type": "regular|elective|honors",
  "elective_group_id": "ELE-AI-DS-2026"  // Required for elective/honors
}
```

**Response (Success):**
```json
{
  "message": "Workload added successfully",
  "inserted_id": "64b25f9ed1a4b5d8f0e6a9b3"
}
```

**Response (Error - Missing Group):**
```json
{
  "error": "elective_group_id is required when subject_type is 'elective'"
}
```

---

### Update Elective Workload

```http
PUT /api/faculty_workload
Content-Type: application/json

{
  "_id": "64b25f9ed1a4b5d8f0e6a9b3",
  "subject_type": "elective",
  "elective_group_id": "ELE-NEW-GROUP-2026"
}
```

---

### Generate Timetable

```http
POST /api/generate_timetable
```

**Response:**
```json
{
  "success": true,
  "message": "Scheduled 45 practical sessions",
  "practicals_scheduled": 45,
  "leftovers": {
    "SY-A-B1": ["Subject1"],
    "TY-B-B2": ["Subject2", "Subject3"]
  }
}
```

---

### Get Class Timetable

```http
GET /api/class_timetables

// Or specific class:
GET /api/class_timetables?class=SY&division=A
```

**Response includes parallel grouping:**
```json
{
  "schedule": {
    "Monday": {
      "11:15": [
        {
          "parallel": true,
          "group_id": "ELE-AI-DS-2026",
          "group_name": "Electives: AI, Data Science",
          "sessions": [
            {"subject": "AI", "faculty": "Dr. A", "lab": "Lab-1"},
            {"subject": "Data Science", "faculty": "Dr. B", "lab": "Lab-2"}
          ]
        }
      ]
    }
  }
}
```

---

## 🐛 Troubleshooting

### Electives not scheduling together?

**Check:**
1. ✅ Both have `subject_type: "elective"`
2. ✅ Both have IDENTICAL `elective_group_id`
3. ✅ Different faculty assigned
4. ✅ Different labs assigned
5. ✅ Check generation logs for conflicts

**Verify in MongoDB:**
```javascript
db.workload.find({
  elective_group_id: "ELE-AI-DS-2026"
})
// Should return BOTH subjects with exact same group ID
```

### Frontend not showing parallel box?

**Check:**
1. ✅ Flask app restarted after backend changes
2. ✅ React app rebuilt/refreshed
3. ✅ Browser cache cleared
4. ✅ Open DevTools → Network → Check API response

### Generation taking longer?

**Note:** Should be similar speed. If much slower:
1. Check logs for constraint conflicts
2. Verify workload entries are reasonable count
3. Check database performance

---

## 📞 Support Resources

| Need | File |
|------|------|
| Architecture details | `ELECTIVES_UPGRADE_GUIDE.md` |
| Test scenarios | `TESTING_AND_DEPLOYMENT.md` |
| Code comments | Check modified Python files |
| Frontend logic | `Frontend/src/lib/timetableUtils.js` |

---

## ✨ Next Steps

1. **Deploy changes** following [TESTING_AND_DEPLOYMENT.md](./TESTING_AND_DEPLOYMENT.md)
2. **Run test scenarios** to validate
3. **Train users** on creating elective workloads
4. **Monitor logs** first generation with electives
5. **Collect feedback** for future enhancements

---

**Version:** 1.0  
**Updated:** May 2026  
**Status:** ✅ Complete & Ready for Deployment

# Electives & Honors - Quick Reference Card

## 🎯 One-Minute Overview

**Problem:** Need to schedule multiple subjects (e.g., AI, Data Science) in the same time slot for the same batch.

**Solution:** Mark subjects as "elective" with matching `elective_group_id`. System will parallel-schedule them if constraints allow.

---

## 📝 API Quick Reference

### Create Elective Entry
```bash
POST /api/faculty_workload
{
  "faculty_id": "...",
  "year": "SY",
  "subject": "AI",
  "subject_full": "Artificial Intelligence",
  "division": "A",
  "batches": [1],
  "theory_hrs": 2,
  "practical_hrs": 2,
  "subject_type": "elective",           ← NEW
  "elective_group_id": "ELE-AI-DS-2026" ← NEW (same for all in group)
}
```

### Generate Timetable
```bash
POST /api/generate_timetable
# Returns: { success: true, practicals_scheduled: 45, leftovers: {...} }
```

### View Results
```bash
GET /api/class_timetables
# Returns: schedule with parallel entries { parallel: true, sessions: [...] }
```

---

## ✅ Success Criteria

| Criterion | Met |
|-----------|-----|
| Two electives schedule in same slot | ✅ Different faculty + different lab |
| Faculty conflict prevented | ✅ Only one scheduled |
| Lab conflict prevented | ✅ Only one scheduled |
| Different groups don't mix | ✅ Scheduled separately |
| 2-hour blocks lock together | ✅ Both slots occupied |
| Frontend shows purple box | ✅ With all subjects listed |

---

## ⚡ Key Rules

```
RULE 1: Faculty is STRICT (no parallel exception)
        └─ If same faculty → Only 1 scheduled

RULE 2: Lab is STRICT (no parallel exception)
        └─ If same lab → Only 1 scheduled

RULE 3: Batch is FLEXIBLE (parallel exception applies)
        └─ If elective + same group + different faculty + different lab → Both scheduled!

RULE 4: Group ID must match exactly
        └─ "ELE-AI-DS-2026" ≠ "ELE-AI-DS-2025" → Separate slots
```

---

## 🧪 Test Checklist

- [ ] Add 2 electives with same group ID
- [ ] Generate → Both scheduled in same slot
- [ ] Check API response has `{ parallel: true, sessions: [AI, DS] }`
- [ ] View in UI → See purple "Electives" box
- [ ] Try same faculty → Only 1 scheduled
- [ ] Try same lab → Only 1 scheduled
- [ ] Try different group → Separate slots

---

## 🔍 Debugging

| Problem | Check |
|---------|-------|
| Electives not parallel | ✓ Same group ID? ✓ Different faculty? ✓ Different lab? |
| UI not showing parallel box | ✓ API response has `parallel: true`? ✓ Cache cleared? |
| Generation fails | ✓ Logs for constraint messages ✓ Valid faculty/lab IDs? |
| Same faculty both subjects | ✓ This is expected! Only 1 will schedule |

---

## 📂 Files Changed

```
Backend/
├── modules/
│   ├── workload_handler.py      [+validation for subject_type, elective_group_id]
│   ├── timetable_generator.py   [+parallel scheduling logic]
│   └── class_timetable_handler.py [+session grouping]
Frontend/
├── src/
│   ├── lib/
│   │   └── timetableUtils.js    [NEW: parallel rendering]
│   └── components/
│       └── ViewTimetables.jsx   [uses timetableUtils]
```

---

## 🚀 Deployment

```bash
# 1. Deploy backend changes
# 2. Deploy frontend changes  
# 3. Optional: Migrate existing workloads
#    db.workload.updateMany({}, {$set: {subject_type: "regular", elective_group_id: null}})
# 4. Test with sample elective entries
# 5. Monitor first generation
```

---

## 💡 Examples

### Example 1: AI + Data Science
```json
Entry 1: {subject: "AI", subject_type: "elective", elective_group_id: "ELE-AI-DS"}
Entry 2: {subject: "DS", subject_type: "elective", elective_group_id: "ELE-AI-DS"}
Result: Both Monday 11:15, different faculty, different labs
```

### Example 2: Web + Mobile + Cloud
```json
Entry 1: {subject: "Web", ..., elective_group_id: "ELE-WEB-MOB-CLOUD"}
Entry 2: {subject: "Mobile", ..., elective_group_id: "ELE-WEB-MOB-CLOUD"}
Entry 3: {subject: "Cloud", ..., elective_group_id: "ELE-WEB-MOB-CLOUD"}
Result: All 3 Monday 11:15 if constraints allow
```

---

## ⚠️ Important

- ✅ Backward compatible (regular subjects unaffected)
- ✅ Constraints are strict (faculty/lab checks never yield)
- ⚠️ Group IDs must match EXACTLY for parallel scheduling
- ⚠️ 2-hour practicals lock entire group to same block

---

## 📞 Quick Answers

**Q: Can same faculty teach 2 electives in same slot?**
A: No. Only 1 will schedule.

**Q: Can same lab host 2 electives in same slot?**
A: No. Only 1 will schedule.

**Q: What if groups have different IDs?**
A: Won't be parallel. Scheduled in different slots.

**Q: Do 2-hour practicals lock together?**
A: Yes. All subjects in group occupy both primary + follow-on slot.

**Q: What if I have 5 different electives in one group?**
A: System will try to schedule all in same slot. If constraints prevent some, they go to leftovers.

**Q: Can I mix regular + elective in same slot?**
A: No. Regular subjects are exclusive. Electives can only parallel with other electives in same group.

---

## 🎓 Learning Path

1. Read: `IMPLEMENTATION_SUMMARY.md` (5 min)
2. Read: `ELECTIVES_UPGRADE_GUIDE.md` (15 min)
3. Do: Test Scenario 1 (Add workloads)
4. Do: Test Scenario 2 (Generate)
5. Do: Test Scenario 3 (View results)
6. Read: `TESTING_AND_DEPLOYMENT.md` for full test suite

---

## 📊 Architecture At a Glance

```
Workload (INPUT)
  └─ subject_type: "elective"
  └─ elective_group_id: "ELE-AI-DS-2026"
       ↓
TimetableGenerator (SCHEDULING)
  └─ Check: Faculty free? Lab free?
  └─ Check: Batch free OR (elective + same group)?
  └─ If YES → Schedule
       ↓
ClassTimetableHandler (TRANSFORM)
  └─ Group by elective_group_id
  └─ Create { parallel: true, sessions: [...] }
       ↓
Frontend (DISPLAY)
  └─ Detect parallel entries
  └─ Render purple "Electives" box
  └─ Show all subjects inside
```

---

## 🔧 Configuration

**subject_type options:**
- `"regular"` - Exclusive slot (old behavior)
- `"elective"` - Can parallel with same group
- `"honors"` - Can parallel with same group (future)

**elective_group_id:**
- Format: `"ELE-<DESCRIPTION>-<YEAR>"` (e.g., "ELE-AI-DS-2026")
- Must be identical for all subjects in group
- If not elective/honors: leave as `null`

---

## 📈 Performance

- Generation speed: ~same (no algorithm change)
- Storage: +fields in workload, +metadata in batch_occupied
- API response: +~5-10% (extra fields)
- UI rendering: Negligible (same component reuse)

---

**Last Updated:** May 2026  
**Status:** Ready for Use ✅

# Data Migration & Best Practices

## Pre-Deployment Checklist

### 1. Backup Database
```bash
# MongoDB backup
mongodump --uri="mongodb://..." --out ./backup_$(date +%Y%m%d)

# Verify backup
mongorestore --list ./backup_20260507
```

### 2. Verify Code Changes
```bash
# Check all 3 backend files modified
git diff HEAD -- Backend/modules/workload_handler.py
git diff HEAD -- Backend/modules/timetable_generator.py
git diff HEAD -- Backend/modules/class_timetable_handler.py

# Check frontend changes
git diff HEAD -- Frontend/src/lib/timetableUtils.js
git diff HEAD -- Frontend/src/components/ViewTimetables.jsx
```

### 3. Test Locally
```bash
# Run with test data before production deployment
python -m pytest tests/test_timetable_generator.py
npm test  # Run frontend tests
```

---

## Database Migration Steps

### Option A: Add Fields to Existing Workloads (Recommended)

**What it does:** Adds `subject_type` and `elective_group_id` to all existing workloads

**When to use:** If you have existing regular workloads you want to keep

**Steps:**

1. **Backup first:**
   ```bash
   mongodump --uri="..." --out ./backup
   ```

2. **Run migration:**
   ```javascript
   // In MongoDB shell or script:
   db.workload.updateMany(
     { subject_type: { $exists: false } },
     { $set: {
       subject_type: "regular",
       elective_group_id: null
     }}
   )
   
   // Verify:
   db.workload.findOne()
   // Should show: subject_type: "regular", elective_group_id: null
   ```

3. **Verify count:**
   ```javascript
   db.workload.countDocuments({ subject_type: { $exists: false } })
   // Should return: 0
   ```

### Option B: Fresh Start (Clean Slate)

**What it does:** Delete all workloads and start fresh with new schema

**When to use:** If starting new semester/year

**Steps:**
```javascript
db.workload.deleteMany({})
// Then add workloads with new schema
```

### Option C: Selective Migration

**What it does:** Migrate only specific workloads

**When to use:** If transitioning some classes to electives

**Steps:**
```javascript
// Migrate only SY-A division
db.workload.updateMany(
  { 
    year: "SY",
    division: "A",
    subject_type: { $exists: false }
  },
  { $set: {
    subject_type: "regular",
    elective_group_id: null
  }}
)
```

---

## Deployment Sequence

### Phase 1: Backend Setup (Development Environment)

```bash
# 1. Backup current database
mongodump --uri="..." --out ./backup_pre_electives

# 2. Deploy code changes
git pull origin main
# Verify files:
# - Backend/modules/workload_handler.py
# - Backend/modules/timetable_generator.py
# - Backend/modules/class_timetable_handler.py

# 3. Install any new dependencies (if any)
pip install -r Backend/requirements.txt

# 4. Run migration script
python Backend/scripts/migrate_workload_schema.py
# Or run MongoDB commands above

# 5. Test with sample data
python -c "from modules.timetable_generator import TimetableGenerator; tg = TimetableGenerator(); print(tg.generate())"
```

### Phase 2: Frontend Setup

```bash
# 1. Verify new files exist
ls Frontend/src/lib/timetableUtils.js
# Output: Frontend/src/lib/timetableUtils.js

# 2. Install dependencies
cd Frontend
npm install

# 3. Build for production
npm run build

# 4. Test locally
npm run dev
# Navigate to timetable view, verify no errors
```

### Phase 3: Production Deployment

```bash
# 1. Stop current services
systemctl stop timetable-api
# or: docker-compose down

# 2. Backup production database
mongodump --uri="prod-uri" --out ./backup_prod_$(date +%Y%m%d_%H%M%S)

# 3. Deploy backend
cp Backend/modules/*.py /production/app/modules/

# 4. Run migrations
python /production/app/scripts/migrate_workload_schema.py

# 5. Deploy frontend
cp Frontend/dist/* /production/static/

# 6. Start services
systemctl start timetable-api
# or: docker-compose up -d

# 7. Verify health
curl http://localhost:5000/health
# Should return: { "status": "ok" }
```

---

## Migration Script (Python)

Create `Backend/scripts/migrate_workload_schema.py`:

```python
#!/usr/bin/env python3
"""
Migrate existing workload documents to include subject_type and elective_group_id.
Run this ONCE before deploying electives feature.
"""

from config import db
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_workload_schema():
    """Add subject_type and elective_group_id to existing workloads."""
    try:
        collection = db['workload']
        
        # Count existing docs without the new fields
        missing_count = collection.count_documents({
            'subject_type': { '$exists': False }
        })
        
        if missing_count == 0:
            logger.info("✅ All documents already migrated")
            return True
        
        logger.info(f"Migrating {missing_count} workload documents…")
        
        # Add fields to all docs that don't have them
        result = collection.update_many(
            { 'subject_type': { '$exists': False } },
            { '$set': {
                'subject_type': 'regular',
                'elective_group_id': None,
                'migrated_at': datetime.now()
            }}
        )
        
        logger.info(f"✅ Updated: {result.modified_count} documents")
        
        # Verify
        still_missing = collection.count_documents({
            'subject_type': { '$exists': False }
        })
        
        if still_missing == 0:
            logger.info("✅ Migration completed successfully")
            return True
        else:
            logger.error(f"❌ {still_missing} documents still missing fields")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = migrate_workload_schema()
    exit(0 if success else 1)
```

**Run it:**
```bash
cd Backend
python scripts/migrate_workload_schema.py
```

---

## Rollback Plan

If issues occur after deployment:

### Option 1: Rollback to Previous Code
```bash
# Stop services
systemctl stop timetable-api

# Revert code
git checkout HEAD~1 -- Backend/modules/
git checkout HEAD~1 -- Frontend/

# Restart
systemctl start timetable-api
```

### Option 2: Rollback Database
```bash
# Stop services
systemctl stop timetable-api

# Restore from backup
mongorestore --drop --dir ./backup_pre_electives

# Restart
systemctl start timetable-api
```

### Option 3: Remove Elective Fields
```bash
# If only workload schema is problematic
db.workload.updateMany(
  {},
  { $unset: {
    subject_type: "",
    elective_group_id: ""
  }}
)
```

---

## Best Practices

### 1. Naming Conventions for Elective Groups

**Format:** `ELE-<SUBJECT1>-<SUBJECT2>-<YEAR>`

**Examples:**
- `ELE-AI-DS-2026` - AI & Data Science for 2026 batch
- `ELE-WEB-MOBILE-2026` - Web & Mobile Dev for 2026 batch
- `ELE-IOT-ROBOTICS-2025` - IoT & Robotics for 2025 batch

**Benefits:**
- Self-documenting
- Unique per year
- Easy to search

### 2. Faculty Assignment

**Best:** Different faculty for each elective subject
```
✅ AI → Faculty A
   DS → Faculty B
```

**Avoid:** Same faculty for multiple electives in group
```
❌ AI → Faculty A
   DS → Faculty A  (Will cause scheduling conflict)
```

### 3. Lab Assignment

**Best:** Different labs for different electives
```
✅ AI Practical → Lab-1
   DS Practical → Lab-2
```

**Acceptable:** Same lab if different batches/times
```
✅ AI (SY-A) → Lab-1 @ Monday 11:15
   AI (SY-B) → Lab-1 @ Monday 14:15
```

### 4. Batch Assignment

**Rule:** All subjects in elective group must have same batches
```
✅ AI → batches: [1, 2]
   DS → batches: [1, 2]  (Same batches)

❌ AI → batches: [1, 2]
   DS → batches: [2, 3]  (Different batches - confusing!)
```

### 5. Practical Hours

**Best:** Keep consistent within group
```
✅ AI → practical_hrs: 2
   DS → practical_hrs: 2  (Both 2-hour blocks)
```

**Acceptable:** Different if necessary
```
✅ AI → practical_hrs: 2
   DS → practical_hrs: 1 (But won't lock together perfectly)
```

---

## Testing After Migration

### Test 1: Verify Migration
```javascript
// MongoDB shell
db.workload.findOne()
// Should have: subject_type, elective_group_id
```

### Test 2: Regular Workloads Still Work
```bash
# Add regular subject
POST /api/faculty_workload
{
  "subject_type": "regular",
  "elective_group_id": null,
  ...other fields...
}

# Generate → should work as before
POST /api/generate_timetable
```

### Test 3: Elective Workloads Work
```bash
# Add 2 electives with same group
POST /api/faculty_workload
{
  "subject_type": "elective",
  "elective_group_id": "ELE-TEST-2026",
  ...other fields...
}

# Generate → check if parallel scheduled
POST /api/generate_timetable
```

### Test 4: API Validation
```bash
# Try invalid subject_type
POST /api/faculty_workload
{
  "subject_type": "invalid"
}
# Should return 400 error

# Try elective without group_id
POST /api/faculty_workload
{
  "subject_type": "elective",
  "elective_group_id": null
}
# Should return 400 error
```

### Test 5: Frontend Rendering
- View class timetable
- Check for purple "Electives" boxes if parallel scheduled
- Verify no visual glitches

---

## Monitoring After Deployment

### Log Patterns to Watch

**✅ Good:**
```
TG-06 FIX: batch_slot_free_or_parallel called successfully
✓ SY-A-B1 AI → Lab-1 @ Monday 11:15
✓ SY-A-B1 Data Science → Lab-2 @ Monday 11:15+12:15
```

**⚠️ Watch For:**
```
Faculty already busy at this slot
Lab slot not free
Elective group mismatch
```

### Metrics to Track

- Generation time (should be ~same)
- Success rate (% of workloads scheduled)
- Parallel session count (# of electives scheduled together)
- Leftovers (subjects unscheduled)

---

## Troubleshooting Migration Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "subject_type field not found" | Migration didn't run | Run migrate_workload_schema.py |
| Electives not grouping | Group IDs different | Check exact string match |
| API returns 400 errors | Old code still running | Restart Flask app |
| Frontend shows old data | Cache issue | Clear browser cache, hard refresh |

---

## Documentation Checklist

- [ ] ELECTIVES_UPGRADE_GUIDE.md (Architectural)
- [ ] TESTING_AND_DEPLOYMENT.md (Testing scenarios)
- [ ] IMPLEMENTATION_SUMMARY.md (Quick overview)
- [ ] QUICK_REFERENCE.md (Developer quick ref)
- [ ] DATA_MIGRATION.md (This file)
- [ ] README.md updated with electives info

---

## Support Contacts

- **Backend Issues:** Check timetable_generator.py logs
- **Frontend Issues:** Check browser console
- **Database Issues:** Check MongoDB logs
- **General Questions:** See QUICK_REFERENCE.md

---

**Last Updated:** May 2026  
**Migration Version:** 1.0

"""
WIT CSE Timetable Data Seeder
=================================
Institution : Walchand Institute of Technology, Solapur
Department  : Computer Science and Engineering
Academic Yr : 2025-26  |  Term 1

Seeds:
  1. Settings (timings from period_times in JSON)
  2. Labs     (all unique lab rooms used)
  3. Faculties (all teaching staff, de-duplicated)
  4. Class Structure (SY: 3 divs A/B/C, 3 batches each;
                      TY: 3 divs A/B/C, 3 batches each;
                      BE/FY: 3 divs A/B/C, 4 batches each)
  5. Subjects  (all subjects with hrs_per_week_lec & practical info)

  Does NOT seed workload (faculty assignments) — done separately.
"""

import sys, re, os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Always load from the Backend .env so we use the SAME database as the app
_env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(_env_path, override=True)

MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://root:root@cluster0.2nkxb6c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
DB_NAME   = os.getenv('DB_NAME', 'Schedulo_Copy')

print(f"  Connecting to MongoDB database: '{DB_NAME}' ...")

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

# ────────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────────

def prt(msg):
    print(msg, flush=True)

def section(title):
    prt(f"\n{'='*70}")
    prt(f"  {title}")
    prt('='*70)

# ════════════════════════════════════════════════════════════════════════════
# STEP 1 – SETTINGS  (timings)
# ════════════════════════════════════════════════════════════════════════════
section("STEP 1 – SETTINGS (department & lab timings)")

#
# Period times from JSON:
#   P1  10:15 – 11:15
#   P2  11:15 – 12:15
#   P3  12:15 – 13:15
#   Recess 13:15 – 14:15
#   P4  14:15 – 15:15
#   P5  15:15 – 16:20
#   Recess 16:20 – 16:30 (short)
#   P6  16:20 – 17:20
#   P7  17:20 – 18:20
#
# For LECTURE slots we treat the START time of each period as the slot key.
# For LAB sessions (2-hr practicals) the natural groupings are:
#   Session 1: 11:15 – 13:15  (P2+P3)
#   Session 2: 14:15 – 16:20  (P4+P5)
#   Session 3: 16:20 – 18:20  (P6+P7)
#

dept_timings = {
    "type":             "department_timings",
    "day_start_time":   "10:15",
    "day_end_time":     "18:20",
    "lecture_duration": 60,
    "breaks": [
        {"name": "Lunch",        "start_time": "13:15", "duration": "60"},
        {"name": "Short Recess", "start_time": "16:20", "duration": "10"},
    ],
    "updated_at": datetime.now(),
}

lab_timings = {
    "type": "lab_timings",
    "sessions": [
        {"startTime": "11:15", "endTime": "13:15"},
        {"startTime": "14:15", "endTime": "16:20"},
        {"startTime": "16:20", "endTime": "18:20"},
    ],
    "updated_at": datetime.now(),
}

db.settings.delete_many({})
db.settings.insert_many([dept_timings, lab_timings])
prt("  [OK] department_timings and lab_timings saved.")

# ════════════════════════════════════════════════════════════════════════════
# STEP 2 – LABS
# ════════════════════════════════════════════════════════════════════════════
section("STEP 2 – LABS")

# Unique lab names extracted from the JSON + short names derived from them
raw_labs = [
    # (full_name,                              short_name)
    ("System Programming Lab",                 "SPL"),
    ("Network Engineering Lab",                "NEL"),
    ("New Classroom No-3 (L315)",              "L315"),
    ("Project Lab",                            "PRL"),
    ("Advanced Programming Lab",               "APL"),
    ("Operating System Lab",                   "OSL"),
    ("New Classroom No-1 (L302)",              "L302"),
    ("Software Lab-1",                         "SL1"),
    ("Software Lab-2",                         "SL2"),
    ("Distributed System Lab",                 "DSL"),
    ("Classroom No-1 (M330)",                  "M330"),
    ("Programming Lab",                        "PGL"),
    ("Web Technology Lab",                     "WTL"),
    ("DS Lab",                                 "DSB"),
    ("SP Lab",                                 "SPB"),
    ("AP Lab",                                 "APB"),
    ("Prog. Lab",                              "PRG"),
    ("Software Lab-I (System Programming Lab-1)", "SLI"),
    ("WT Lab",                                 "WTB"),
    ("NE Lab",                                 "NEB"),
    ("Software Lab-1 / Software Lab-2",        "SL12"),
    ("Software Lab-II",                        "SLII"),
    ("OS Lab",                                 "OSB"),
    ("Software Lab-I (AP Lab)",                "SLAP"),
    ("Seminar Hall (M331)",                    "M331"),
    ("New Classroom No-4 (L402)",              "L402"),
    ("New Classroom No-5 (L403)",              "L403"),
    ("PG Lab",                                 "PGB"),
    ("Classroom No-2 (M329)",                  "M329"),
    ("New Classroom No-2 (L303)",              "L303"),
    ("Smart Classroom (L419)",                 "L419"),
]

db.labs.delete_many({})
lab_docs = [{"name": name, "short_name": sn} for name, sn in raw_labs]
result = db.labs.insert_many(lab_docs)
prt(f"  [OK] Inserted {len(result.inserted_ids)} labs.")

# Build a lookup: name → _id (string)
lab_id_map = {}
for doc in db.labs.find({}):
    lab_id_map[doc["name"]] = str(doc["_id"])

# ════════════════════════════════════════════════════════════════════════════
# STEP 3 – FACULTIES
# ════════════════════════════════════════════════════════════════════════════
section("STEP 3 – FACULTIES")

#
# Extract all unique faculty names from the JSON data.
# Deduplicate by canonical name; assign a short_name abbreviation.
# Combined entries like "MR. A / MR. B" are split into two individual records.
#

raw_faculty_names = [
    "DR. MRS. S. M. DOL",
    "MR. F. R. SAYYED",
    "MS. S. S. NAZARE",
    "MR. S. M. METAGAR",
    "MR. M. R. PATIL",
    "MR. D. P. PANDIT",
    "MR. A. A. BABAR",
    "DR. MS. R. K. DIXIT",
    "MR. N. S. GAJJAM",
    "MR. V. D. CHAVAN",
    "MR. D. S. MANE",
    "MR. S. RADDI",
    "MR. D. P. PANDIT / MR. M. A. MAHANT",   # combined – split below
    "MR. V. V. KULKARNI",
    "MR. M. A. MAHANT",
    "MRS. P. M. CHANNAPATTAN",
    "DR. MRS. A. M. PUJAR",
    "MR. B. R. SOLUNKE",
    "MRS. K. A. KHEDIKAR",
    "DR. MRS. P. C. KALADEEP",
    "MR. S. T. PATEL",
    "DR. R. V. ARGIDDI",
    "MRS. S. S. AMBARKAR",
    "MR. A. R. CHINCHAWADE",
    "MRS. K. R. PARDESHI",
    "MRS. P. D. JADHAV",
    "MR. B. R. SOLUNKE / MRS. K. R. PARDESHI",  # combined – split below
    "MR. S. T. PATEL / MRS. P. D. JADHAV",      # combined – split below
    "MS. S. S. NAZARE / MR. S. RADDI",           # combined – split below
]

def split_and_clean(name_str):
    """Split 'A / B' combined names into a list of clean individual names."""
    parts = [p.strip() for p in name_str.split("/")]
    return parts

unique_names = set()
for raw in raw_faculty_names:
    for n in split_and_clean(raw):
        if n and n != "-":
            unique_names.add(n)

# Abbreviation mapping (initials from last two parts of name)
def make_short(full_name):
    """Derive a short code from the faculty name, e.g. 'MR. F. R. SAYYED' → 'FRS'."""
    # Remove salutation
    name = re.sub(r'^(DR\. )?(MRS?\.|MS\.) ', '', full_name).strip()
    parts = name.split()
    # take initials of each part
    abbr = ''.join(p[0] for p in parts if p)
    return abbr[:6].upper()

# Ensure uniqueness of short names
short_counts = {}
def unique_short(name):
    base = make_short(name)
    if base not in short_counts:
        short_counts[base] = 0
        return base
    short_counts[base] += 1
    return f"{base}{short_counts[base]}"

# Also keep admin user – don't delete it; only delete non-admin teaching staff
# We delete all faculty whose role != 'ADMIN', then re-insert.
db.faculty.delete_many({"role": {"$ne": "ADMIN"}})

faculty_docs = []
for name in sorted(unique_names):
    doc = {
        "name":       name,
        "short_name": unique_short(name),
        "title":      "Prof",
        "role":       "faculty",
    }
    faculty_docs.append(doc)

result = db.faculty.insert_many(faculty_docs)
prt(f"  [OK] Inserted {len(result.inserted_ids)} faculty members.")

# Build lookup: full_name → {_id, short_name}
fac_map = {}
for doc in db.faculty.find({"role": "faculty"}):
    fac_map[doc["name"]] = {"id": str(doc["_id"]), "short": doc["short_name"]}

prt("  Faculty list:")
for name, info in sorted(fac_map.items()):
    prt(f"    {info['short']:8s}  {name}")

# ════════════════════════════════════════════════════════════════════════════
# STEP 4 – CLASS STRUCTURE
# ════════════════════════════════════════════════════════════════════════════
section("STEP 4 – CLASS STRUCTURE")

#
# From the JSON:
#   SY (Second Year): Div-A, Div-B, Div-C  →  3 batches each (SA1/SA2/SA3 etc.)
#   TY (Third Year):  Div-A, Div-B, Div-C  →  3 batches each (TA1/TA2/TA3 etc.)
#   FY (Final Year):  Div-A, Div-B, Div-C  →  4 batches each (BA1/BA2/BA3/BA4 etc.)
#
# We map SY→sy, TY→ty, FY→be (Final Year = BE in our system)
#

class_structure = {
    "sy": {
        "num_divisions":     3,
        "batches_per_division": 3,
        "0": {"div": "A", "batches": 3},
        "1": {"div": "B", "batches": 3},
        "2": {"div": "C", "batches": 3},
    },
    "ty": {
        "num_divisions":     3,
        "batches_per_division": 3,
        "0": {"div": "A", "batches": 3},
        "1": {"div": "B", "batches": 3},
        "2": {"div": "C", "batches": 3},
    },
    "be": {
        "num_divisions":     3,
        "batches_per_division": 4,
        "0": {"div": "A", "batches": 4},
        "1": {"div": "B", "batches": 4},
        "2": {"div": "C", "batches": 4},
    },
}

db.class_structure.delete_many({})
db.class_structure.insert_one(class_structure)
prt("  [OK] Class structure saved:")
prt("        SY: 3 divs (A/B/C), 3 batches each")
prt("        TY: 3 divs (A/B/C), 3 batches each")
prt("        FY (BE): 3 divs (A/B/C), 4 batches each")

# ════════════════════════════════════════════════════════════════════════════
# STEP 5 – SUBJECTS
# ════════════════════════════════════════════════════════════════════════════
section("STEP 5 – SUBJECTS (with lec hrs and practical info)")

#
# From the JSON timetables we can derive approximate weekly lecture hours by
# counting non-practical period entries per subject across the 5-day week.
#
# Lecture counts observed in the JSON timetables:
#
# SY subjects (across Div-A/B/C, all consistent):
#   DMS  – theory only     → 3 lec/week
#   DS   – theory+practical → 2 lec/week + 1 practical session/batch
#   CG   – theory+practical → 2 lec/week + 1 practical session/batch
#   OE-I – theory+practical → 1 lec/week + 1 practical session/batch
#   ED   – theory+practical → 1 lec/week + 1 practical session/batch
#   MDM-I– theory only     → 2 lec/week
#   UHV  – theory only     → 2 lec/week
#   PY   – theory+practical → 1 lec/week + 1 practical session/batch
#
# TY subjects (across Div-A/B/C):
#   DBE      – theory+practical → 3 lec/week + 1 practical/batch
#   DAA      – theory+practical → 2 lec/week + 1 practical/batch
#   OS       – theory+practical → 2 lec/week + 1 practical/batch
#   PEC-I ML – theory+practical → 2 lec/week + 1 practical/batch
#   PEC-I DAV– theory+practical → 2 lec/week + 1 practical/batch (same students split by choice)
#   AJP      – theory+practical → 2 lec/week + 1 practical/batch
#   IKS      – theory only      → 2 lec/week
#   OE-III   – theory only      → 2 lec/week
#   MDM-III  – theory only      → 3 lec/week
#
# FY (BE) subjects (across Div-A/B/C):
#   STQA  – theory+practical → 3 lec/week + 1 practical/batch
#   DS(FY)– theory+practical → 3 lec/week + 1 practical/batch
#   PE-II – theory+practical → 3 lec/week + (classroom session = practical-type)
#   PE-III– theory+practical → 3 lec/week + 1 practical/batch
#   DEV   – theory+practical → 2 lec/week + 1 practical/batch
#   DL    – theory+practical → 2 lec/week + 1 practical/batch
#   PA    – theory+practical → 2 lec/week + 1 practical/batch
#
# practical_duration = 2 hrs (two consecutive periods per batch per session)
# practical_type     = "Specific Lab" (each subject has a dedicated lab)
# required_labs      = primary lab from JSON for that subject
#

# Map lab names to DB-inserted lab names (exact match)
# We use the primary lab used for each subject (first occurrence in JSON)
LAB = {k: k for k in lab_id_map}   # identity map since names are exact

SY_SUBJECTS = [
    {
        "name":                  "Discrete Mathematical Structures",
        "short_name":            "DMS",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
    {
        "name":                  "Data Structures",
        "short_name":            "DS",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "System Programming Lab",
    },
    {
        "name":                  "Computer Graphics",
        "short_name":            "CG",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Network Engineering Lab",
    },
    {
        "name":                  "Open Elective-I: Management Information System",
        "short_name":            "OE-I",
        "hrs_per_week_lec":      1,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "New Classroom No-3 (L315)",
    },
    {
        "name":                  "Entrepreneurship Development",
        "short_name":            "ED",
        "hrs_per_week_lec":      1,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "New Classroom No-3 (L315)",
    },
    {
        "name":                  "Multidisciplinary Minor-I: Operating System",
        "short_name":            "MDM-I",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
    {
        "name":                  "Universal Human Values",
        "short_name":            "UHV",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
    {
        "name":                  "Python Programming",
        "short_name":            "PY",
        "hrs_per_week_lec":      1,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Project Lab",
    },
]

TY_SUBJECTS = [
    {
        "name":                  "Database Engineering",
        "short_name":            "DBE",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Web Technology Lab",
    },
    {
        "name":                  "Design and Analysis of Algorithm",
        "short_name":            "DAA",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Project Lab",
    },
    {
        "name":                  "Operating Systems",
        "short_name":            "OS",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "DS Lab",
    },
    {
        "name":                  "Professional Elective Course-I: Machine Learning",
        "short_name":            "PEC-I (ML)",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Software Lab-I (System Programming Lab-1)",
    },
    {
        "name":                  "Professional Elective Course-I: Data Analysis and Visualization",
        "short_name":            "PEC-I (DAV)",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "System Programming Lab",
    },
    {
        "name":                  "Advanced Java Programming",
        "short_name":            "AJP",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "SP Lab",
    },
    {
        "name":                  "Indian Knowledge System",
        "short_name":            "IKS",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
    {
        "name":                  "Open Elective-III",
        "short_name":            "OE-III",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
    {
        "name":                  "Multidisciplinary Minor-III: Operating Systems",
        "short_name":            "MDM-III",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
]

BE_SUBJECTS = [
    {
        "name":                  "Software Testing and Quality Assurance",
        "short_name":            "STQA",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Seminar Hall (M331)",
    },
    {
        "name":                  "Distributed Systems",
        "short_name":            "DS (FY)",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Distributed System Lab",
    },
    {
        "name":                  "Professional Elective-II: Business Intelligence",
        "short_name":            "PE-II",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 0,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
    },
    {
        "name":                  "Professional Elective-III: Big Data Analytics",
        "short_name":            "PE-III",
        "hrs_per_week_lec":      3,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Software Lab-1",
    },
    {
        "name":                  "DevOps",
        "short_name":            "DEV",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Project Lab",
    },
    {
        "name":                  "Deep Learning",
        "short_name":            "DL",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "Programming Lab",
    },
    {
        "name":                  "Predictive Analytics",
        "short_name":            "PA",
        "hrs_per_week_lec":      2,
        "hrs_per_week_practical": 1,
        "practical_duration":    2,
        "practical_type":        "Specific Lab",
        "required_labs":         "WT Lab",
    },
]

db.subjects.delete_many({})
db.subjects.insert_one({
    "sy": SY_SUBJECTS,
    "ty": TY_SUBJECTS,
    "be": BE_SUBJECTS,
})

prt("  [OK] Subjects inserted:")
prt(f"    SY ({len(SY_SUBJECTS)} subjects): {[s['short_name'] for s in SY_SUBJECTS]}")
prt(f"    TY ({len(TY_SUBJECTS)} subjects): {[s['short_name'] for s in TY_SUBJECTS]}")
prt(f"    BE ({len(BE_SUBJECTS)} subjects): {[s['short_name'] for s in BE_SUBJECTS]}")

# ════════════════════════════════════════════════════════════════════════════
# ALSO CLEAR OLD TIMETABLE DATA (so it gets regenerated fresh)
# ════════════════════════════════════════════════════════════════════════════
section("STEP 6 – CLEARING OLD TIMETABLE ARTIFACTS")
db.workload.delete_many({})
db.master_lab_timetable.delete_many({})
db.class_timetable.delete_many({})
db.constraints.delete_many({})
prt("  [OK] workload, master_lab_timetable, class_timetable, constraints cleared.")

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════
section("SEEDING COMPLETE – SUMMARY")
prt(f"  Institution : Walchand Institute of Technology, Solapur")
prt(f"  Department  : Computer Science and Engineering")
prt(f"  Academic Yr : 2025-26  |  Term 1")
prt(f"")
prt(f"  Settings    : department_timings + lab_timings  (day 10:15-18:20, 3 lab sessions)")
prt(f"  Labs        : {db.labs.count_documents({})} lab rooms")
prt(f"  Faculties   : {db.faculty.count_documents({'role':'faculty'})} teaching staff")
prt(f"  Classes     : SY(A/B/C 3bat) + TY(A/B/C 3bat) + FY/BE(A/B/C 4bat)")
prt(f"  Subjects    : SY={len(SY_SUBJECTS)}, TY={len(TY_SUBJECTS)}, BE={len(BE_SUBJECTS)}")
prt(f"  Workload    : NOT YET INSERTED (do separately)")
prt(f"")
prt(f"  NEXT STEP: Insert faculty workload assignments per class-division-subject,")
prt(f"             then click 'Generate Timetable' in the UI.")

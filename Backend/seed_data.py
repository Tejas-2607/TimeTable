"""
seed_data.py
Wipes the entire MongoDB database and seeds it with realistic CS Department data:
  - Settings/timings
  - Class structure: FY (2 divs), SY (2 divs), TY (1 div), BE (1 div)
  - Labs
  - Subjects per year with proper hrs_per_week_lec and hrs_per_week_practical
  - Faculty — several are SHARED across multiple years (the key stress-test)
  - Faculty workload assignments
  - Special constraints (preferred_off and fixed_time)

Usage:
  cd Backend && source .venv/bin/activate && python3 seed_data.py
"""

from config import db
from bson import ObjectId
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# 1. WIPE all collections
# ──────────────────────────────────────────────────────────────────────────────
COLLECTIONS = [
    'settings', 'class_structure', 'subjects', 'faculty', 'labs',
    'workload', 'constraints', 'class_timetable', 'master_lab_timetable',
]
for col in COLLECTIONS:
    db[col].drop()
print("✅ Dropped all collections")


# ──────────────────────────────────────────────────────────────────────────────
# 2. SETTINGS  (9:15 – 17:15, 60min slots, 1hr lunch break at 13:15)
# ──────────────────────────────────────────────────────────────────────────────
db['settings'].insert_one({
    'type': 'department_timings',
    'lecture_duration': 60,
    'day_start_time': '09:15',
    'day_end_time': '17:15',
    'breaks': [
        {'name': 'Lunch', 'start_time': '13:15', 'duration': 60}
    ],
    'updated_at': datetime.now(),
})
print("✅ Settings seeded  (09:15–17:15, 7 lecture slots, lunch at 13:15)")


# ──────────────────────────────────────────────────────────────────────────────
# 3. CLASS STRUCTURE
#    FY: 2 divisions (A, B), 2 batches each
#    SY: 2 divisions (A, B), 2 batches each
#    TY: 1 division  (A),    2 batches
#    BE: 1 division  (A),    2 batches
# ──────────────────────────────────────────────────────────────────────────────
db['class_structure'].insert_one({
    'FY': {'num_divisions': 2, 'batches_per_division': 2, '0': {'div': 'A', 'batches': 2}, '1': {'div': 'B', 'batches': 2}},
    'SY': {'num_divisions': 2, 'batches_per_division': 2, '0': {'div': 'A', 'batches': 2}, '1': {'div': 'B', 'batches': 2}},
    'TY': {'num_divisions': 1, 'batches_per_division': 2, '0': {'div': 'A', 'batches': 2}},
    'BE': {'num_divisions': 1, 'batches_per_division': 2, '0': {'div': 'A', 'batches': 2}},
})
print("✅ Class structure seeded  (FY/SY: 2 divs × 2 batches; TY/BE: 1 div × 2 batches)")


# ──────────────────────────────────────────────────────────────────────────────
# 4. LABS
# ──────────────────────────────────────────────────────────────────────────────
labs = [
    {'name': 'Computer Lab 1',  'capacity': 30},
    {'name': 'Computer Lab 2',  'capacity': 30},
    {'name': 'Network Lab',     'capacity': 25},
    {'name': 'Electronics Lab', 'capacity': 25},
]
db['labs'].insert_many(labs)
print(f"✅ {len(labs)} labs seeded")


# ──────────────────────────────────────────────────────────────────────────────
# 5. FACULTY  (some are shared across years — this is the stress test)
#    Shared: Prof. Kumar (FY+SY), Dr. Mehta (SY+TY), Prof. Joshi (SY+TY+BE),
#            Dr. Verma (SY+TY), Dr. Sharma (FY only — teaches Math for all FY divs)
# ──────────────────────────────────────────────────────────────────────────────
faculty_records = [
    # id alias        full_name                  short  specialisation
    ('FAC001', 'Dr. Sharma',    'Rajesh Sharma',        'RS',   'Mathematics'),
    ('FAC002', 'Prof. Kumar',   'Anil Kumar',           'AK',   'Programming'),   # FY + SY
    ('FAC003', 'Dr. Patel',     'Nita Patel',           'NP',   'Electronics'),
    ('FAC004', 'Prof. Singh',   'Harpreet Singh',       'HS',   'Communication'),
    ('FAC005', 'Prof. Gupta',   'Sunita Gupta',         'SG',   'Computer Organization'),
    ('FAC006', 'Dr. Mehta',     'Vijay Mehta',          'VM',   'Systems'),       # SY + TY
    ('FAC007', 'Prof. Joshi',   'Priya Joshi',          'PJ',   'Networks'),      # SY + TY + BE
    ('FAC008', 'Dr. Verma',     'Rakesh Verma',         'RV',   'Database/ML'),   # SY + TY
    ('FAC009', 'Prof. Desai',   'Meera Desai',          'MD',   'Software Engg'),
    ('FAC010', 'Dr. Nair',      'Suresh Nair',          'SN',   'AI/ML'),
]
faculty_id_map = {}  # short_id → ObjectId string

# Add a dedicated admin user for testing/management
from werkzeug.security import generate_password_hash
admin_oid = ObjectId()
db['faculty'].insert_one({
    '_id': admin_oid,
    'name': 'Admin User',
    'full_name': 'System Administrator',
    'short_name': 'ADMIN',
    'email': 'admin@college.edu',
    'password': generate_password_hash('admin123'),
    'role': 'admin',
    'created_at': datetime.now()
})
faculty_id_map['ADMIN'] = str(admin_oid)

for fac_id, title_name, full_name, short, spec in faculty_records:
    oid = ObjectId()
    db['faculty'].insert_one({
        '_id': oid,
        'name': title_name,
        'full_name': full_name,
        'short_name': short,
        'email': f"{short.lower()}@college.edu",
        'specialisation': spec,
    })
    faculty_id_map[fac_id] = str(oid)

print(f"✅ {len(faculty_records)} faculty seeded  (4 shared across years)")


# ──────────────────────────────────────────────────────────────────────────────
# 6. SUBJECTS
#    Each subject: name, short_name, hrs_per_week_lec, hrs_per_week_practical,
#                  practical_duration (slots per session), practical_type,
#                  required_labs (if Specific Lab)
# ──────────────────────────────────────────────────────────────────────────────
subjects_doc = {
    # ── FY ──────────────────────────────────────────────────────────────────
    'FY': [
        {
            '_id': str(ObjectId()),
            'name': 'Engineering Mathematics I',
            'short_name': 'MATHS',
            'hrs_per_week_lec': 4,
            'hrs_per_week_practical': 0,   # no practicals
            'practical_duration': 0,
            'practical_type': 'None',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Programming Fundamentals',
            'short_name': 'PF',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,   # 1 practical session/week
            'practical_duration': 2,       # 2 consecutive slots per session
            'practical_type': 'Specific Lab',
            'required_labs': 'Computer Lab 1',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Basic Electronics',
            'short_name': 'BE',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Specific Lab',
            'required_labs': 'Electronics Lab',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Communication Skills',
            'short_name': 'CS',
            'hrs_per_week_lec': 2,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Computer Organization',
            'short_name': 'CO',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Common Lab',
        },
    ],
    # ── SY ──────────────────────────────────────────────────────────────────
    'SY': [
        {
            '_id': str(ObjectId()),
            'name': 'Data Structures',
            'short_name': 'DS',
            'hrs_per_week_lec': 4,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Specific Lab',
            'required_labs': 'Computer Lab 1',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Database Management Systems',
            'short_name': 'DBMS',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Specific Lab',
            'required_labs': 'Computer Lab 2',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Operating Systems',
            'short_name': 'OS',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Common Lab',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Computer Networks',
            'short_name': 'CN',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Discrete Mathematics',
            'short_name': 'DM',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
    ],
    # ── TY ──────────────────────────────────────────────────────────────────
    'TY': [
        {
            '_id': str(ObjectId()),
            'name': 'Machine Learning',
            'short_name': 'ML',
            'hrs_per_week_lec': 4,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Specific Lab',
            'required_labs': 'Computer Lab 2',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Software Engineering',
            'short_name': 'SE',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Compiler Design',
            'short_name': 'CD',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Specific Lab',
            'required_labs': 'Network Lab',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Artificial Intelligence',
            'short_name': 'AI',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
    ],
    # ── BE ──────────────────────────────────────────────────────────────────
    'BE': [
        {
            '_id': str(ObjectId()),
            'name': 'Network Security',
            'short_name': 'NS',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Specific Lab',
            'required_labs': 'Network Lab',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Cloud Computing',
            'short_name': 'CC',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
        {
            '_id': str(ObjectId()),
            'name': 'Project Management',
            'short_name': 'PM',
            'hrs_per_week_lec': 2,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        },
    ],
}
db['subjects'].insert_one(subjects_doc)
total_subj = sum(len(v) for v in subjects_doc.items() if isinstance(v, list))
print(f"✅ Subjects seeded  (FY:{len(subjects_doc['FY'])}, SY:{len(subjects_doc['SY'])}, TY:{len(subjects_doc['TY'])}, BE:{len(subjects_doc['BE'])})")


# ──────────────────────────────────────────────────────────────────────────────
# 7. FACULTY WORKLOAD ASSIGNMENTS
#    Covers SHARED faculty across years (stress test):
#      Prof. Kumar → FY-PF, SY-DS
#      Dr. Mehta   → SY-OS, TY-SE
#      Prof. Joshi → SY-CN, TY-CD, BE-NS
#      Dr. Verma   → SY-DBMS, TY-ML
#    Each entry: year, division, subject, faculty_id, batches, theory_hrs, practical_hrs
# ──────────────────────────────────────────────────────────────────────────────
workloads = []

def W(year, division, subject, fac_id_key, batches, theory_hrs, practical_hrs):
    """Helper to create a workload dict."""
    return {
        'year': year,
        'division': division,
        'subject': subject,
        'subject_full': subject,  # will be resolved from subject map in generator
        'faculty_id': faculty_id_map[fac_id_key],
        'batches': batches,
        'theory_hrs': theory_hrs,
        'practical_hrs': practical_hrs,
    }

# ── FY Division A ────────────────────────────────────────────────────────────
workloads += [
    W('FY', 'A', 'MATHS', 'FAC001', [],              4, 0),
    W('FY', 'A', 'PF',    'FAC002', ['Batch 1', 'Batch 2'], 3, 1),
    W('FY', 'A', 'BE',    'FAC003', ['Batch 1', 'Batch 2'], 3, 1),
    W('FY', 'A', 'CS',    'FAC004', [],              2, 0),
    W('FY', 'A', 'CO',    'FAC005', ['Batch 1', 'Batch 2'], 3, 1),
]

# ── FY Division B ────────────────────────────────────────────────────────────
workloads += [
    W('FY', 'B', 'MATHS', 'FAC001', [],              4, 0),   # Dr. Sharma teaches BOTH FY divs
    W('FY', 'B', 'PF',    'FAC002', ['Batch 1', 'Batch 2'], 3, 1),  # Prof. Kumar teaches BOTH FY divs
    W('FY', 'B', 'BE',    'FAC003', ['Batch 1', 'Batch 2'], 3, 1),
    W('FY', 'B', 'CS',    'FAC004', [],              2, 0),
    W('FY', 'B', 'CO',    'FAC005', ['Batch 1', 'Batch 2'], 3, 1),
]

# ── SY Division A ────────────────────────────────────────────────────────────
workloads += [
    W('SY', 'A', 'DS',   'FAC002', ['Batch 1', 'Batch 2'], 4, 1),   # Prof. Kumar → also FY
    W('SY', 'A', 'DBMS', 'FAC008', ['Batch 1', 'Batch 2'], 3, 1),
    W('SY', 'A', 'OS',   'FAC006', ['Batch 1', 'Batch 2'], 3, 1),   # Dr. Mehta → also TY
    W('SY', 'A', 'CN',   'FAC007', [],              3, 0),            # Prof. Joshi → also TY+BE
    W('SY', 'A', 'DM',   'FAC001', [],              3, 0),            # Dr. Sharma → also FY
]

# ── SY Division B ────────────────────────────────────────────────────────────
workloads += [
    W('SY', 'B', 'DS',   'FAC002', ['Batch 1', 'Batch 2'], 4, 1),
    W('SY', 'B', 'DBMS', 'FAC008', ['Batch 1', 'Batch 2'], 3, 1),
    W('SY', 'B', 'OS',   'FAC006', ['Batch 1', 'Batch 2'], 3, 1),
    W('SY', 'B', 'CN',   'FAC007', [],              3, 0),
    W('SY', 'B', 'DM',   'FAC001', [],              3, 0),
]

# ── TY Division A ────────────────────────────────────────────────────────────
workloads += [
    W('TY', 'A', 'ML',  'FAC008', ['Batch 1', 'Batch 2'], 4, 1),    # Dr. Verma → also SY
    W('TY', 'A', 'SE',  'FAC006', [],              3, 0),              # Dr. Mehta → also SY
    W('TY', 'A', 'CD',  'FAC007', ['Batch 1', 'Batch 2'], 3, 1),     # Prof. Joshi → also SY+BE
    W('TY', 'A', 'AI',  'FAC010', [],              3, 0),
]

# ── BE Division A ────────────────────────────────────────────────────────────
workloads += [
    W('BE', 'A', 'NS',  'FAC007', ['Batch 1', 'Batch 2'], 3, 1),     # Prof. Joshi → also SY+TY
    W('BE', 'A', 'CC',  'FAC009', [],              3, 0),
    W('BE', 'A', 'PM',  'FAC004', [],              2, 0),
]

db['workload'].insert_many(workloads)
print(f"✅ {len(workloads)} workload entries seeded  (shared faculty across FY/SY/TY/BE)")


# ──────────────────────────────────────────────────────────────────────────────
# 8. SPECIAL CONSTRAINTS
#    preferred_off: faculty unavailable at that slot
#    fixed_time:    force a subject at a specific slot
# ──────────────────────────────────────────────────────────────────────────────
constraints = [
    # Dr. Sharma (RS) not available Monday morning (religious commitment)
    {
        'type': 'preferred_off',
        'faculty_name': 'Dr. Sharma',
        'day': 'Monday',
        'time_slot': '09:15',
        'reason': 'Religious commitment',
    },
    # Prof. Kumar (AK) not available Friday afternoon (research meeting)
    {
        'type': 'preferred_off',
        'faculty_name': 'Prof. Kumar',
        'day': 'Friday',
        'time_slot': '15:15',
        'reason': 'Research meeting',
    },
    {
        'type': 'preferred_off',
        'faculty_name': 'Prof. Kumar',
        'day': 'Friday',
        'time_slot': '16:15',
        'reason': 'Research meeting',
    },
    # SY-A OS practical must be on Wednesday 09:15 (lab booking constraint)
    {
        'type': 'fixed_time',
        'year': 'SY',
        'division': 'A',
        'subject': 'OS',
        'faculty_name': 'Dr. Mehta',
        'day': 'Wednesday',
        'time_slot': '09:15',
        'reason': 'Lab already booked',
    },
]
db['constraints'].insert_many(constraints)
print(f"✅ {len(constraints)} constraints seeded")


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SEED COMPLETE — Summary")
print("="*60)
print(f"  Timings:     09:15–17:15, 7 lecture slots, lunch 13:15")
print(f"  Years:       FY, SY, TY, BE")
print(f"  Divisions:   FY/SY→A,B   TY/BE→A")
print(f"  Labs:        {', '.join(l['name'] for l in labs)}")
print(f"  Faculty:     {len(faculty_records)}  (4 shared across years)")
print(f"  Subjects:    FY={len(subjects_doc['FY'])}, SY={len(subjects_doc['SY'])}, TY={len(subjects_doc['TY'])}, BE={len(subjects_doc['BE'])}")
print(f"  Workloads:   {len(workloads)}")
print(f"  Constraints: {len(constraints)}")
print("="*60)
print("\nShared faculty (conflict stress test):")
print("  FAC001 Dr. Sharma  → FY-MATHS(A+B)  + SY-DM(A+B)")
print("  FAC002 Prof. Kumar → FY-PF(A+B)     + SY-DS(A+B)")
print("  FAC006 Dr. Mehta   → SY-OS(A+B)     + TY-SE(A)")
print("  FAC007 Prof. Joshi → SY-CN(A+B)     + TY-CD(A) + BE-NS(A)")
print("  FAC008 Dr. Verma   → SY-DBMS(A+B)   + TY-ML(A)")
print("\nRun generation:")
print("  1. POST /api/generate              (master practical timetable)")
print("  2. POST /api/generate_class_timetables  (class-level practicals)")
print("  3. POST /api/generate_lectures     (lecture timetable)")

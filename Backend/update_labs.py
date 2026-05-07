import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME   = os.getenv('DB_NAME', 'Schedulo_Copy')
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
print(f"DB: {DB_NAME}")

# ── STEP 1: Replace labs ──────────────────────────────────────────────────
LABS = [
    ("System Programming Lab",      "SPL"),
    ("Network Engineering Lab",     "NEL"),
    ("Project Lab",                 "PRL"),
    ("Advanced Programming Lab",    "APL"),
    ("Operating System Lab",        "OSL"),
    ("Software Lab-1",              "SL1"),
    ("Software Lab-2",              "SL2"),
    ("Distributed System Lab",      "DSL"),
    ("Programming Lab",             "PGL"),
    ("Web Technology Lab",          "WTL"),
    ("New Classroom No-3 (L315)",   "L315"),
    ("New Classroom No-1 (L302)",   "L302"),
    ("Classroom No-1 (M330)",       "M330"),
    ("Seminar Hall (M331)",         "M331"),
    ("New Classroom No-4 (L402)",   "L402"),
    ("New Classroom No-5 (L403)",   "L403"),
    ("Smart Classroom (L419)",      "L419"),
    ("Classroom No-2 (M329)",       "M329"),
]

db.labs.delete_many({})
db.labs.insert_many([{"name": n, "short_name": s} for n, s in LABS])
print(f"[OK] Inserted {len(LABS)} labs")

# ── STEP 2: Update subjects.required_labs to only use labs from above list ─
# Mapping: subject short_name → required_labs (name from above, or None)
# Logic from JSON:
#   SY: DS→SPL, CG→NEL, OE-I→L315(classroom), ED→L315(classroom), PY→PRL
#   TY: DBE→WTL, DAA→PRL, OS→OSL(closest), PEC-I(ML)→SL1, PEC-I(DAV)→SPL, AJP→APL
#   BE: STQA→M331(classroom), DS(FY)→DSL, PE-III→SL1, DEV→PRL, DL→PGL

SUBJ_LAB = {
    # SY
    "DMS":          None,
    "DS":           "System Programming Lab",
    "CG":           "Network Engineering Lab",
    "OE-I":         "New Classroom No-3 (L315)",
    "ED":           "New Classroom No-3 (L315)",
    "MDM-I":        None,
    "UHV":          None,
    "PY":           "Project Lab",
    # TY
    "DBE":          "Web Technology Lab",
    "DAA":          "Project Lab",
    "OS":           "Operating System Lab",
    "PEC-I (ML)":   "Software Lab-1",
    "PEC-I (DAV)":  "System Programming Lab",
    "AJP":          "Advanced Programming Lab",
    "IKS":          None,
    "OE-III":       None,
    "MDM-III":      None,
    # BE / FY
    "STQA":         "Seminar Hall (M331)",
    "DS (FY)":      "Distributed System Lab",
    "PE-II":        None,
    "PE-III":       "Software Lab-1",
    "DEV":          "Project Lab",
    "DL":           "Programming Lab",
    "PA":           None,
}

subj_doc = db.subjects.find_one({})
if not subj_doc:
    print("ERROR: No subjects document found!")
    exit(1)

def patch_list(subj_list):
    for s in subj_list:
        sn = s.get("short_name")
        lab = SUBJ_LAB.get(sn)
        if lab:
            s["required_labs"] = lab
        elif "required_labs" in s:
            del s["required_labs"]
    return subj_list

updated = {
    "sy": patch_list(subj_doc.get("sy", [])),
    "ty": patch_list(subj_doc.get("ty", [])),
    "be": patch_list(subj_doc.get("be", [])),
}

db.subjects.update_one({"_id": subj_doc["_id"]}, {"$set": updated})
print("[OK] Subjects updated with new required_labs")

# Print summary
for yr, subjs in updated.items():
    for s in subjs:
        lab = s.get("required_labs", "(none)")
        print(f"  {yr.upper()} | {s['short_name']:12s} | {lab}")

print("\nDone.")

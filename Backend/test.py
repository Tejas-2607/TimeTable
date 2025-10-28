"""
Run this in your Flask shell or as a separate Python script
to debug what's in your database
"""

from config import db
import json

# Check subjects collection
print("=" * 60)
print("SUBJECTS COLLECTION")
print("=" * 60)

subjects_doc = db['subjects'].find_one({})
if subjects_doc:
    print(json.dumps(subjects_doc, indent=2, default=str))
else:
    print("NO SUBJECTS FOUND!")

# Check class structure
print("\n" + "=" * 60)
print("CLASS STRUCTURE COLLECTION")
print("=" * 60)

class_struct = db['class_structure'].find_one({})
if class_struct:
    print(json.dumps(class_struct, indent=2, default=str))
else:
    print("NO CLASS STRUCTURE FOUND!")

# Check faculty
print("\n" + "=" * 60)
print("FACULTY COLLECTION")
print("=" * 60)

faculties = list(db['faculty'].find({}, {'_id': 0}))
if faculties:
    print(json.dumps(faculties, indent=2, default=str))
else:
    print("NO FACULTIES FOUND!")

# Check labs
print("\n" + "=" * 60)
print("LABS COLLECTION")
print("=" * 60)

labs = list(db['labs'].find({}, {'_id': 0}))
if labs:
    print(json.dumps(labs, indent=2, default=str))
else:
    print("NO LABS FOUND!")

# Check workload
print("\n" + "=" * 60)
print("WORKLOAD COLLECTION")
print("=" * 60)

workloads = list(db['workload'].find({}, {'_id': 0}))
if workloads:
    print(json.dumps(workloads, indent=2, default=str))
else:
    print("NO WORKLOADS FOUND!")
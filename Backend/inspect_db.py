from config import db
from pprint import pprint

print("--- COMPUTER LAB 2 - MONDAY ---")
doc = db['master_lab_timetable'].find_one({'lab_name': 'Computer Lab 2'})
if doc:
    sched = doc.get('schedule', {}).get('Monday', {})
    for slot in sorted(sched.keys()):
        print(f"  {slot}: {sched[slot]}")

print("\n--- SY-A CLASS TT - MONDAY ---")
tt = db['class_timetable'].find_one({'class': 'SY', 'division': 'A'})
if tt:
    sched = tt.get('schedule', {}).get('Monday', {})
    for slot in sorted(sched.keys()):
        print(f"  {slot}: {sched[slot]}")

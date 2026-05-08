import os
import sys
import json
from datetime import datetime

# Add Backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

# Set MongoDB connection
os.environ['MONGO_URI'] = 'mongodb+srv://vamsiv:adithi@timetable.3fbdm.mongodb.net/timetable_db?retryWrites=true&w=majority'

from config import db
from modules.timetable_generator import TimetableGenerator
from modules.lecture_tt_generator import LectureTimetableGenerator

print("=" * 80)
print("GENERATING PRACTICAL TIMETABLES")
print("=" * 80)

try:
    gen_practical = TimetableGenerator()
    result_practical = gen_practical.generate()
    print(f"\nPractical Generation Result:")
    print(json.dumps(result_practical, indent=2, default=str))
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("GENERATING LECTURE TIMETABLES")
print("=" * 80)

try:
    gen_lecture = LectureTimetableGenerator()
    result_lecture = gen_lecture.generate()
    print(f"\nLecture Generation Result:")
    print(json.dumps(result_lecture, indent=2, default=str))
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Export all class timetables
print("\n" + "=" * 80)
print("EXPORTING TIMETABLES")
print("=" * 80)

try:
    class_timetables = list(db['class_timetable'].find({}))
    # Remove MongoDB ObjectId
    data = []
    for tt in class_timetables:
        tt_copy = dict(tt)
        tt_copy['_id'] = str(tt_copy['_id'])
        data.append(tt_copy)
    
    with open('result_class_tt.json', 'w') as f:
        json.dump({'timetables': data}, f, indent=2, default=str)
    
    print(f"\n✓ Exported {len(class_timetables)} class timetables to result_class_tt.json")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

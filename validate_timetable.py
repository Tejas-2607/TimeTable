import json
import sys
from collections import defaultdict

def validate_timetable(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    timetables = data.get('timetables', [])

    # Trackers for clashes
    faculty_schedule = defaultdict(lambda: defaultdict(list))  # faculty -> day -> slots
    lab_schedule = defaultdict(lambda: defaultdict(list))      # lab -> day -> slots
    class_schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # (class, division) -> day -> slot -> subjects

    clashes = {
        'faculty_clashes': [],
        'lab_clashes': [],
        'duplicate_lectures': [],
        'duplicate_practicals': []
    }

    for tt in timetables:
        class_name = tt['class']
        division = tt['division']
        schedule = tt['schedule']

        for day, slots in schedule.items():
            for slot, sessions in slots.items():
                if not sessions:
                    continue

                # Check for duplicate subjects in same slot for same class
                subjects_in_slot = []
                for session in sessions:
                    subject = session['subject']
                    session_type = session.get('type', 'practical')

                    if subject in subjects_in_slot:
                        if session_type == 'lecture':
                            clashes['duplicate_lectures'].append({
                                'class': class_name,
                                'division': division,
                                'day': day,
                                'slot': slot,
                                'subject': subject
                            })
                        else:
                            clashes['duplicate_practicals'].append({
                                'class': class_name,
                                'division': division,
                                'day': day,
                                'slot': slot,
                                'subject': subject
                            })
                    subjects_in_slot.append(subject)

                # Check faculty clashes
                for session in sessions:
                    faculty = session['faculty']
                    faculty_schedule[faculty][day].append(slot)

                    # Check if faculty has multiple sessions at same time
                    if len(faculty_schedule[faculty][day]) > 1:
                        # Check for overlapping slots
                        slots_for_faculty = faculty_schedule[faculty][day]
                        if len(set(slots_for_faculty)) < len(slots_for_faculty):
                            clashes['faculty_clashes'].append({
                                'faculty': faculty,
                                'day': day,
                                'slots': slots_for_faculty
                            })

                # Check lab clashes
                for session in sessions:
                    if 'lab' in session:
                        lab = session['lab']
                        lab_schedule[lab][day].append(slot)

                        # Check if lab has multiple sessions at same time
                        if len(lab_schedule[lab][day]) > 1:
                            slots_for_lab = lab_schedule[lab][day]
                            if len(set(slots_for_lab)) < len(slots_for_lab):
                                clashes['lab_clashes'].append({
                                    'lab': lab,
                                    'day': day,
                                    'slots': slots_for_lab
                                })

    # Remove duplicates from clash lists
    for key in clashes:
        unique_clashes = []
        seen = set()
        for clash in clashes[key]:
            clash_tuple = tuple(sorted(clash.items()))
            if clash_tuple not in seen:
                seen.add(clash_tuple)
                unique_clashes.append(clash)
        clashes[key] = unique_clashes

    return clashes

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_timetable.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    clashes = validate_timetable(json_file)

    print("Validation Results:")
    print("=" * 50)

    total_clashes = sum(len(v) for v in clashes.values())

    if total_clashes == 0:
        print("✅ No clashes found!")
    else:
        print(f"❌ Found {total_clashes} clashes:")

        if clashes['faculty_clashes']:
            print(f"\nFaculty clashes ({len(clashes['faculty_clashes'])}):")
            for clash in clashes['faculty_clashes']:
                print(f"  - {clash['faculty']} on {clash['day']} at slots: {clash['slots']}")

        if clashes['lab_clashes']:
            print(f"\nLab clashes ({len(clashes['lab_clashes'])}):")
            for clash in clashes['lab_clashes']:
                print(f"  - {clash['lab']} on {clash['day']} at slots: {clash['slots']}")

        if clashes['duplicate_lectures']:
            print(f"\nDuplicate lectures ({len(clashes['duplicate_lectures'])}):")
            for clash in clashes['duplicate_lectures']:
                print(f"  - {clash['class']}-{clash['division']} {clash['subject']} on {clash['day']} {clash['slot']}")

        if clashes['duplicate_practicals']:
            print(f"\nDuplicate practicals ({len(clashes['duplicate_practicals'])}):")
            for clash in clashes['duplicate_practicals']:
                print(f"  - {clash['class']}-{clash['division']} {clash['subject']} on {clash['day']} {clash['slot']}")
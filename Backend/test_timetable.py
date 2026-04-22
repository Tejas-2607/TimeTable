"""
test_timetable.py
Comprehensive pytest test suite for the timetable generation system.

Tests cover:
  POSITIVE tests — valid data should generate without conflicts
  NEGATIVE tests — invalid/conflicting data should be caught or rejected

Run:
  cd Backend && source .venv/bin/activate
  pip install pytest
  python3 seed_data.py          # ensure DB is seeded
  # Start Flask in another terminal, then:
  pytest test_timetable.py -v
"""

import pytest
import requests
from collections import defaultdict
from config import db

BASE = "http://localhost:5001/api"

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _get_all_timetables():
    """Return list of all class timetable docs from DB."""
    tts = list(db['class_timetable'].find({}))
    for t in tts:
        t['_id'] = str(t['_id'])
    return tts

def _get_master_timetables():
    """Return list of all master lab timetable docs from DB."""
    return list(db['master_lab_timetable'].find({}))

def _get_all_schedule_entries():
    """
    Flatten ALL sessions across all timetables into a list of dicts:
    {year, division, day, slot, subject, faculty, type, lab, batch}
    """
    entries = []
    for tt in _get_all_timetables():
        year = tt['class']
        div  = tt['division']
        for day, slots in tt.get('schedule', {}).items():
            for slot, sessions in slots.items():
                for sess in sessions:
                    if sess:  # skip empty
                        entries.append({
                            'year':     year,
                            'division': div,
                            'day':      day,
                            'slot':     slot,
                            'subject':  sess.get('subject'),
                            'faculty':  sess.get('faculty'),
                            'type':     sess.get('type', 'lecture'),
                            'lab':      sess.get('lab'),
                            'batch':    sess.get('batch'),
                        })
    return entries


# ──────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────────────────────────

def _get_admin_headers():
    """Login as admin and return Authorization headers."""
    r = requests.post(f"{BASE}/auth/authenticate", json={
        'email': 'admin@college.edu',
        'password': 'admin123'
    })
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    token = r.json().get('token')
    return {'Authorization': f'Bearer {token}'}

# ──────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session', autouse=True)
def generate_timetables():
    """Generate timetables once before all tests."""
    headers = _get_admin_headers()
    
    # MAIN ENDPOINT: Regenerates EVERYTHING (Practical + Class TT + Lectures)
    r = requests.post(
        f"{BASE}/regenerate_master_practical_timetable",
        headers=headers
    )
    assert r.status_code in (201, 206), f"Timetable generation failed: {r.text}"
    data = r.json()
    assert "message" in data, f"Generation error: {data}"

    yield  # tests run here


# ──────────────────────────────────────────────────────────────────────────────
# ────────────────── POSITIVE TESTS ──────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

class TestAPISanity:
    """Basic API health checks."""

    def test_get_subjects_returns_all_years(self):
        r = requests.get(f"{BASE}/subjects")
        assert r.status_code == 200
        data = r.json()
        for yr in ('FY', 'SY', 'TY', 'BE'):
            assert yr in data, f"Year {yr} missing from /api/subjects"
            assert len(data[yr]) > 0, f"No subjects for {yr}"

    def test_get_faculty_returns_all(self):
        r = requests.get(f"{BASE}/faculty")
        assert r.status_code == 200
        data = r.json()
        faculty_list = data if isinstance(data, list) else data.get('faculty', [])
        assert len(faculty_list) == 11, f"Expected 11 faculty (10 seeded + 1 admin), got {len(faculty_list)}"

    def test_get_labs_returns_all(self):
        r = requests.get(f"{BASE}/labs")
        assert r.status_code == 200
        data = r.json()
        labs = data if isinstance(data, list) else data.get('labs', [])
        assert len(labs) == 4, f"Expected 4 labs, got {len(labs)}"

    def test_class_structure_has_four_years(self):
        r = requests.get(f"{BASE}/class_structure")
        assert r.status_code == 200
        data = r.json()
        for yr in ('FY', 'SY', 'TY', 'BE'):
            assert yr in data, f"{yr} missing from class structure"

    def test_class_timetables_generated(self):
        tts = _get_all_timetables()
        # FY: A,B  SY: A,B  TY: A  BE: A → 6 class timetables
        assert len(tts) >= 6, f"Expected at least 6 class timetables, got {len(tts)}"

    def test_master_lab_timetables_generated(self):
        master = _get_master_timetables()
        lab_names = {m['lab_name'] for m in master}
        assert len(lab_names) > 0, "No lab timetables generated"


class TestHoursRespected:
    """Verify that hrs_per_week_lec and hrs_per_week_practical are followed."""

    def test_lectures_per_week_match_requirement(self):
        """Each subject should have exactly hrs_per_week_lec lecture slots in the week."""
        subjects_doc = db['subjects'].find_one({})
        expected = {}
        for yr, subj_list in subjects_doc.items():
            if yr == '_id':
                continue
            for s in subj_list:
                lec_hrs = s.get('hrs_per_week_lec', 0)
                if lec_hrs > 0:
                    expected[(yr, s['short_name'])] = lec_hrs

        entries = _get_all_schedule_entries()
        lecture_counts = defaultdict(int)
        for e in entries:
            if e['type'] == 'lecture' and e['subject']:
                # Count per (year, div, subject) per week
                lecture_counts[(e['year'], e['division'], e['subject'])] += 1

        errors = []
        for (yr, sn), req in expected.items():
            # Check across all divisions of that year
            tt_keys = [(yr, d) for d in ('A', 'B') if db['class_timetable'].find_one({'class': yr, 'division': d})]
            for yr2, div in tt_keys:
                count = lecture_counts.get((yr2, div, sn), 0)
                if count != req:
                    errors.append(f"{yr2}-{div} {sn}: expected {req} lectures, got {count}")

        assert not errors, "Lecture hour mismatches:\n" + "\n".join(errors)

    def test_practical_sessions_per_week_match_requirement(self):
        """Each subject should have exactly hrs_per_week_practical practical sessions scheduled."""
        subjects_doc = db['subjects'].find_one({})

        # Get timings to determine start slots
        from modules import settings_handler
        timings = settings_handler.get_timings()
        _, lec_slots, _ = settings_handler.calculate_slots(timings)
        start_slots = set(lec_slots)

        entries = _get_all_schedule_entries()
        # Only count primary-slot practicals
        # Only count primary-slot practicals (to avoid double-counting 2-hr sessions)
        # A practical is a 'start' if its slot is e.g. '09:15', '11:15', '14:15'...
        # Actually, let's use the START_SLOTS from settings but just make sure we only count once.
        seen_sessions = set()
        for e in entries:
            if e['type'] == 'practical' and e['subject']:
                # session_key: (year, div, batch, subject, day) - only one entry per day
                sess_key = (e['year'], e['division'], e['batch'], e['subject'], e['day'])
                if sess_key not in seen_sessions:
                    practical_counts[(e['year'], e['division'], e['batch'], e['subject'])] += 1
                    seen_sessions.add(sess_key)

        errors = []
        for yr, subj_list in subjects_doc.items():
            if yr == '_id':
                continue
            for s in subj_list:
                prac_per_week = s.get('hrs_per_week_practical', 0)
                if prac_per_week == 0:
                    continue
                # Check relevant workloads
                workloads = list(db['workload'].find({'year': yr, 'subject': s['short_name']}))
                for w in workloads:
                    div = w['division']
                    batches = w.get('batches', [])
                    for b in batches:
                        # Normalize batch naming
                        batch_label = b if b.startswith('Batch') else f"Batch {b}"
                        count = practical_counts.get((yr, div, batch_label, s['short_name']), 0)
                        if count != prac_per_week:
                            errors.append(
                                f"{yr}-{div}-{batch_label} {s['short_name']}: "
                                f"expected {prac_per_week} practical(s), got {count}"
                            )
        assert not errors, "Practical session mismatches:\n" + "\n".join(errors)


class TestNoConflicts:
    """Verify there are no scheduling conflicts."""

    def test_no_faculty_double_booking(self):
        """A faculty member must not teach two classes at the same day+slot."""
        entries = _get_all_schedule_entries()
        # Group by (day, slot, faculty)
        slot_faculty: dict = defaultdict(list)
        for e in entries:
            if e['faculty']:
                slot_faculty[(e['day'], e['slot'], e['faculty'])].append(
                    f"{e['year']}-{e['division']} {e['subject']} ({e['type']})"
                )
        conflicts = {
            k: v for k, v in slot_faculty.items()
            if len(v) > 1
        }
        assert not conflicts, (
            "Faculty double-booked:\n" +
            "\n".join(f"  {k[2]} on {k[0]} @ {k[1]}: {v}" for k, v in conflicts.items())
        )

    def test_no_lab_double_booking(self):
        """A lab must not be booked for two different batches at the same day+slot."""
        master = _get_master_timetables()
        conflicts = []
        for lab_doc in master:
            lab_name = lab_doc['lab_name']
            for day, slots in lab_doc.get('schedule', {}).items():
                for slot, sessions in slots.items():
                    if len(sessions) > 1:
                        groups = [f"{s.get('class')}-{s.get('division')}-B{s.get('batch')} {s.get('subject')}"
                                  for s in sessions]
                        conflicts.append(f"  {lab_name} on {day} @ {slot}: {groups}")
        assert not conflicts, "Lab double-booked:\n" + "\n".join(conflicts)

    def test_no_class_slot_has_multiple_lectures(self):
        """A class (year-division) must not have more than one lecture in the same slot."""
        entries = [e for e in _get_all_schedule_entries() if e['type'] == 'lecture']
        slot_class: dict = defaultdict(list)
        for e in entries:
            slot_class[(e['year'], e['division'], e['day'], e['slot'])].append(e['subject'])
        conflicts = {k: v for k, v in slot_class.items() if len(v) > 1}
        assert not conflicts, (
            "Multiple lectures in same slot:\n" +
            "\n".join(f"  {k}: {v}" for k, v in conflicts.items())
        )

    def test_no_same_subject_twice_in_one_day(self):
        """A subject should not appear more than once per day for the same class."""
        entries = [e for e in _get_all_schedule_entries() if e['type'] == 'lecture']
        # Group by (year, div, day, subject) → count
        day_subj: dict = defaultdict(int)
        for e in entries:
            day_subj[(e['year'], e['division'], e['day'], e['subject'])] += 1
        duplicates = {k: v for k, v in day_subj.items() if v > 1}
        assert not duplicates, (
            "Same subject appears multiple times on the same day:\n" +
            "\n".join(f"  {k}: {v} times" for k, v in duplicates.items())
        )

    def test_no_batch_double_booked(self):
        """A (year, division, batch) must not have two practicals at the same day+slot."""
        entries = [e for e in _get_all_schedule_entries() if e['type'] == 'practical']
        slot_batch: dict = defaultdict(list)
        for e in entries:
            if e['batch']:
                slot_batch[(e['year'], e['division'], e['batch'], e['day'], e['slot'])].append(e['subject'])
        conflicts = {k: v for k, v in slot_batch.items() if len(v) > 1}
        assert not conflicts, (
            "Batch double-booked for practicals:\n" +
            "\n".join(f"  {k}: {v}" for k, v in conflicts.items())
        )


class TestSpecialConstraints:
    """Verify special constraints are respected."""

    def test_dr_sharma_not_scheduled_monday_0915(self):
        """Dr. Sharma has preferred_off on Monday 09:15 — must not be scheduled there."""
        entries = _get_all_schedule_entries()
        violations = [
            e for e in entries
            if e['faculty'] == 'Dr. Sharma'
            and e['day'] == 'Monday'
            and e['slot'] == '09:15'
        ]
        assert not violations, (
            f"Dr. Sharma scheduled despite preferred_off on Monday 09:15: {violations}"
        )

    def test_prof_kumar_not_scheduled_friday_1515_1615(self):
        """Prof. Kumar has preferred_off on Friday 15:15 and 16:15."""
        entries = _get_all_schedule_entries()
        violations = [
            e for e in entries
            if e['faculty'] == 'Prof. Kumar'
            and e['day'] == 'Friday'
            and e['slot'] in ('15:15', '16:15')
        ]
        assert not violations, (
            f"Prof. Kumar scheduled despite preferred_off: {violations}"
        )

    def test_sy_a_os_fixed_wednesday_0915(self):
        """SY-A OS practical must be on Wednesday 09:15 (fixed_time constraint)."""
        entries = _get_all_schedule_entries()
        os_practicals = [
            e for e in entries
            if e['year'] == 'SY'
            and e['division'] == 'A'
            and e['subject'] == 'OS'
            and e['type'] == 'practical'
        ]
        if not os_practicals:
            pytest.skip("No OS practicals found for SY-A (may not have been scheduled)")

        # At least one OS session must be at Wednesday 09:15
        matches = [e for e in os_practicals if e['day'] == 'Wednesday' and e['slot'] == '09:15']
        assert matches, (
            f"SY-A OS not scheduled at Wednesday 09:15 (fixed_time constraint). "
            f"Actual slots: {[(e['day'], e['slot']) for e in os_practicals]}"
        )


class TestSharedFacultyIntegrity:
    """Specifically test scenarios where faculty teach multiple years."""

    def test_prof_kumar_no_conflict_fy_and_sy(self):
        """Prof. Kumar teaches FY-PF and SY-DS — must never have conflict."""
        entries = _get_all_schedule_entries()
        kumar_slots = defaultdict(list)
        for e in entries:
            if e['faculty'] == 'Prof. Kumar':
                kumar_slots[(e['day'], e['slot'])].append(
                    f"{e['year']}-{e['division']} {e['subject']}"
                )
        conflicts = {k: v for k, v in kumar_slots.items() if len(v) > 1}
        assert not conflicts, (
            "Prof. Kumar (shared FY+SY) has conflicts:\n" +
            "\n".join(f"  {k}: {v}" for k, v in conflicts.items())
        )

    def test_dr_mehta_no_conflict_sy_and_ty(self):
        """Dr. Mehta teaches SY-OS and TY-SE — must never have conflict."""
        entries = _get_all_schedule_entries()
        mehta_slots = defaultdict(list)
        for e in entries:
            if e['faculty'] == 'Dr. Mehta':
                mehta_slots[(e['day'], e['slot'])].append(
                    f"{e['year']}-{e['division']} {e['subject']}"
                )
        conflicts = {k: v for k, v in mehta_slots.items() if len(v) > 1}
        assert not conflicts, (
            "Dr. Mehta (shared SY+TY) has conflicts:\n" +
            "\n".join(f"  {k}: {v}" for k, v in conflicts.items())
        )

    def test_prof_joshi_no_conflict_sy_ty_be(self):
        """Prof. Joshi teaches SY-CN, TY-CD, BE-NS — must never have conflict."""
        entries = _get_all_schedule_entries()
        joshi_slots = defaultdict(list)
        for e in entries:
            if e['faculty'] == 'Prof. Joshi':
                joshi_slots[(e['day'], e['slot'])].append(
                    f"{e['year']}-{e['division']} {e['subject']}"
                )
        conflicts = {k: v for k, v in joshi_slots.items() if len(v) > 1}
        assert not conflicts, (
            "Prof. Joshi (shared SY+TY+BE) has conflicts:\n" +
            "\n".join(f"  {k}: {v}" for k, v in conflicts.items())
        )

    def test_dr_sharma_no_conflict_fy_and_sy(self):
        """Dr. Sharma teaches FY-MATHS (A+B) and SY-DM (A+B) — no conflict."""
        entries = _get_all_schedule_entries()
        sharma_slots = defaultdict(list)
        for e in entries:
            if e['faculty'] == 'Dr. Sharma':
                sharma_slots[(e['day'], e['slot'])].append(
                    f"{e['year']}-{e['division']} {e['subject']}"
                )
        conflicts = {k: v for k, v in sharma_slots.items() if len(v) > 1}
        assert not conflicts, (
            "Dr. Sharma (shared FY+SY, 2 FY divs) has conflicts:\n" +
            "\n".join(f"  {k}: {v}" for k, v in conflicts.items())
        )


class TestBreakSlots:
    """No session should be scheduled during lunch break."""

    def test_no_session_during_lunch(self):
        """13:15 is lunch break — no lectures or practicals at this slot."""
        entries = _get_all_schedule_entries()
        lunch_sessions = [e for e in entries if e['slot'] == '13:15' and e['subject']]
        assert not lunch_sessions, (
            f"Sessions scheduled during lunch break (13:15): {lunch_sessions}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# ────────────────── NEGATIVE TESTS ──────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

class TestNegativeSubject:
    """Test that invalid subject data is rejected by the API."""

    def test_add_subject_missing_year(self):
        """Missing 'year' field should return 400."""
        headers = _get_admin_headers()
        r = requests.post(f"{BASE}/subjects", headers=headers, json={
            'name': 'Test Subject',
            'short_name': 'TS',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Common Lab',
        })
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_add_subject_invalid_year(self):
        """Invalid year string should return 400."""
        headers = _get_admin_headers()
        r = requests.post(f"{BASE}/subjects", headers=headers, json={
            'year': 'INVALID_YEAR',
            'name': 'Test Subject',
            'short_name': 'TS',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Common Lab',
        })
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_add_duplicate_subject_short_name(self):
        """Adding a subject with an already-existing short_name should return 409."""
        headers = _get_admin_headers()
        r = requests.post(f"{BASE}/subjects", headers=headers, json={
            'year': 'SY',
            'name': 'Data Structures Duplicate',
            'short_name': 'DS',          # already exists in SY
            'hrs_per_week_lec': 4,
            'hrs_per_week_practical': 1,
            'practical_duration': 2,
            'practical_type': 'Common Lab',
        })
        assert r.status_code == 409, f"Expected 409 (duplicate), got {r.status_code}: {r.text}"

    def test_add_subject_missing_name(self):
        """Missing 'name' field should return 400."""
        headers = _get_admin_headers()
        r = requests.post(f"{BASE}/subjects", headers=headers, json={
            'year': 'SY',
            'short_name': 'TS2',
            'hrs_per_week_lec': 3,
            'hrs_per_week_practical': 0,
            'practical_duration': 0,
            'practical_type': 'None',
        })
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"


class TestNegativeFaculty:
    """Test faculty endpoint input validation."""

    def test_add_faculty_empty_body(self):
        """Empty body should return 400."""
        headers = _get_admin_headers()
        r = requests.post(f"{BASE}/faculty", headers=headers, json={})
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"

    def test_delete_faculty_invalid_id(self):
        """Invalid ObjectId for delete should return 400."""
        headers = _get_admin_headers()
        r = requests.delete(f"{BASE}/faculty", headers=headers, json={'_id': 'not-a-valid-id'})
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"


class TestNegativeGeneration:
    """Test that generation fails gracefully when data is missing."""

    def test_lecture_generation_idempotent(self):
        """Running generation twice should not create duplicate lectures."""
        headers = _get_admin_headers()
        # Run generation again
        r = requests.post(f"{BASE}/regenerate_master_practical_timetable", headers=headers)
        assert r.status_code in (201, 206)
        data = r.json()
        assert "message" in data

        # Verify still no duplicate
        entries = [e for e in _get_all_schedule_entries() if e['type'] == 'lecture']
        slot_class: dict = defaultdict(list)
        for e in entries:
            slot_class[(e['year'], e['division'], e['day'], e['slot'])].append(e['subject'])
        conflicts = {k: v for k, v in slot_class.items() if len(v) > 1}
        assert not conflicts, f"Duplicates after re-generation: {conflicts}"

    def test_semester_workload_api_missing_faculty(self):
        """Workload addition with missing faculty_id should return 400."""
        headers = _get_admin_headers()
        r = requests.post(f"{BASE}/faculty_workload", headers=headers, json={
            'year': 'SY',
            'subject': 'DS',
        })
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"


class TestDataIntegrity:
    """Basic data integrity checks."""

    def test_subjects_doc_has_correct_years(self):
        """Subjects document in DB must have all 4 years as keys."""
        doc = db['subjects'].find_one({})
        assert doc is not None, "No subjects document found"
        for yr in ('FY', 'SY', 'TY', 'BE'):
            assert yr in doc, f"Year {yr} missing from subjects document"

    def test_each_year_has_subjects(self):
        """Each year must have at least 2 subjects."""
        doc = db['subjects'].find_one({})
        for yr in ('FY', 'SY', 'TY', 'BE'):
            assert len(doc[yr]) >= 2, f"Year {yr} has fewer than 2 subjects"

    def test_workload_faculty_ids_valid(self):
        """All faculty_id references in workload must match actual faculty documents."""
        faculty_ids = {str(f['_id']) for f in db['faculty'].find({})}
        for w in db['workload'].find({}):
            fid = str(w.get('faculty_id', ''))
            assert fid in faculty_ids, (
                f"Workload {w.get('year')}-{w.get('division')}-{w.get('subject')} "
                f"has unknown faculty_id: {fid}"
            )

    def test_practical_subjects_have_required_lab_in_db(self):
        """Subjects with 'Specific Lab' type must reference a lab that actually exists in DB."""
        lab_names = {l['name'] for l in db['labs'].find({})}
        doc = db['subjects'].find_one({})
        errors = []
        for yr, subj_list in doc.items():
            if yr == '_id':
                continue
            for s in subj_list:
                if s.get('practical_type') == 'Specific Lab':
                    req = s.get('required_labs')
                    if req and req not in lab_names:
                        errors.append(f"{yr}-{s['short_name']} requires '{req}' which does not exist")
        assert not errors, "Required labs not found in DB:\n" + "\n".join(errors)

    def test_timetable_covers_all_classes(self):
        """Every year-division combination must have a generated timetable."""
        expected = [
            ('FY', 'A'), ('FY', 'B'),
            ('SY', 'A'), ('SY', 'B'),
            ('TY', 'A'),
            ('BE', 'A'),
        ]
        tts = _get_all_timetables()
        found = {(t['class'], t['division']) for t in tts}
        missing = [f"{y}-{d}" for y, d in expected if (y, d) not in found]
        assert not missing, f"Missing class timetables for: {missing}"

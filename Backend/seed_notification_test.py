from config import db
from bson import ObjectId
from datetime import datetime, timedelta

def seed_data():
    print("Seeding test data for notifications...")
    
    # 1. Create/Update a test faculty
    test_faculty = {
        "name": "Test Notification Faculty",
        "short_name": "TNF",
        "email": "a.ankita0910@gmail.com", # Using email found in .env
        "role": "faculty"
    }
    
    # Check if they exist
    existing = db.faculty.find_one({"email": test_faculty["email"]})
    if existing:
        faculty_id = existing["_id"]
        db.faculty.update_one({"_id": faculty_id}, {"$set": test_faculty})
        print(f"Updated existing faculty with ID: {faculty_id}")
    else:
        result = db.faculty.insert_one(test_faculty)
        faculty_id = result.inserted_id
        print(f"Created new faculty with ID: {faculty_id}")

    # 2. Add a lecture to class_timetable starting soon
    # Current time is around 18:32. 
    # Let's set a lecture for 18:40 (8 minutes from now).
    # The notification should trigger when "now + 5 mins" == 18:40, so at 18:35.
    
    target_time_str = "18:40"
    day_of_week = datetime.now().strftime("%A")
    
    test_timetable = {
        "class": "TEST",
        "division": "Z",
        "class_key": "TEST-Z",
        "schedule": {
            day_of_week: {
                target_time_str: [
                    {
                        "subject_full": "Notification Testing",
                        "subject": "NOTIF",
                        "faculty_id": str(faculty_id),
                        "type": "lecture"
                    }
                ]
            }
        }
    }
    
    # Remove old test timetable
    db.class_timetable.delete_many({"class": "TEST", "division": "Z"})
    
    # Insert new one
    db.class_timetable.insert_one(test_timetable)
    print(f"Added test lecture for {day_of_week} at {target_time_str}")

if __name__ == "__main__":
    seed_data()

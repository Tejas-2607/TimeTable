from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
import logging
from config import db, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER

logger = logging.getLogger(__name__)

# Initialize Mail and Scheduler (they will be tied to app in app.py)
mail = Mail()
scheduler = APScheduler()

def send_reminder_email(faculty_email, faculty_name, lecture_details):
    """Send an email reminder to the faculty."""
    try:
        subject = f"Reminder: Upcoming Lecture - {lecture_details['subject_full']}"
        
        # Determine if it's a practical or lecture
        type_str = lecture_details.get('type', 'lecture').capitalize()
        
        body = f"""
        Dear {faculty_name},

        This is a reminder for your upcoming {type_str} session.

        Details:
        - Subject: {lecture_details['subject_full']} ({lecture_details['subject']})
        - Class: {lecture_details['class_key']}
        - Time: {lecture_details['time']}
        - Location: {lecture_details.get('lab', 'Classroom')}
        - Batch: {lecture_details.get('batch', 'N/A')}

        Please be ready 5 minutes before the start time.

        Regards,
        Timetable Management System
        """
        
        msg = Message(subject, recipients=[faculty_email], body=body)
        mail.send(msg)
        logger.info(f"✓ Reminder email sent to {faculty_name} ({faculty_email}) for {lecture_details['subject']}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to send email to {faculty_email}: {e}")
        return False

def check_and_send_reminders():
    """Background job to check for lectures starting in 5 minutes."""
    with scheduler.app.app_context():
        now = datetime.now()
        # Calculate the target time (5 minutes from now)
        target_time = now + timedelta(minutes=5)
        
        # We need the time in "HH:MM" format as stored in the JSON/DB
        target_time_str = target_time.strftime("%H:%M")
        day_of_week = now.strftime("%A") # e.g., "Monday"
        
        logger.info(f"Notification Check: {day_of_week} at {target_time_str} (Now: {now.strftime('%H:%M')})")
        
        # Collections
        class_timetable_col = db['class_timetable']
        faculty_col = db['faculty']
        
        # Query all class timetables
        timetables = list(class_timetable_col.find({}))
        
        sent_count = 0
        for tt in timetables:
            schedule = tt.get('schedule', {})
            day_schedule = schedule.get(day_of_week, {})
            
            # Check if there's a lecture at the target time
            # Note: The DB stores times as keys like "10:15", "11:15", etc.
            # If the current time + 5 mins matches exactly, or if we want to be more flexible:
            # For simplicity, we match the exact key.
            if target_time_str in day_schedule:
                lectures = day_schedule[target_time_str]
                
                if not isinstance(lectures, list):
                    # Handle single object if it's not a list (though schema says list)
                    lectures = [lectures]
                
                for lecture in lectures:
                    if not lecture: continue
                    
                    faculty_id = lecture.get('faculty_id')
                    if faculty_id:
                        # Fetch faculty email
                        from bson import ObjectId
                        faculty = faculty_col.find_one({"_id": ObjectId(faculty_id)})
                        
                        if faculty and faculty.get('email'):
                            faculty_email = faculty['email']
                            faculty_name = faculty.get('name', 'Faculty Member')
                            
                            # Add time and class_key to lecture details for the email body
                            lecture['time'] = target_time_str
                            lecture['class_key'] = tt.get('class_key', f"{tt.get('class')}-{tt.get('division')}")
                            
                            if send_reminder_email(faculty_email, faculty_name, lecture):
                                sent_count += 1
        
        if sent_count > 0:
            logger.info(f"Total reminders sent in this cycle: {sent_count}")

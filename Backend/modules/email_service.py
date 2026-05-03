from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")


def send_email(to, subject, html_content):
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        body = getattr(e, 'body', None)
        print(f"[email_service] Error sending email: {e}")
        if body:
            print(f"[email_service] SendGrid response body: {body}")
        return None


def send_faculty_welcome_email(faculty_name, faculty_email):
    subject = "Welcome to Schedulo – Your Faculty Account Has Been Created"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Welcome to Schedulo, {faculty_name}!</h2>
        <p>Your faculty account has been created by the admin.</p>
        <p>You can now log in to the Schedulo Timetable System using the following credentials:</p>
        <p style="background: #f4f4f4; padding: 10px; border-radius: 4px;">
            <strong>Email:</strong> {faculty_email}<br>
            <strong>Default Password:</strong> password123
        </p>
        <p style="color: #e74c3c; font-weight: bold;">IMPORTANT: Please reset your password on first login for security.</p>
        <p>If you have any questions, please contact your administrator.</p>
        <br>
        <p style="color: #7f8c8d; font-size: 12px;">This is an automated message from Schedulo.</p>
    </div>
    """
    return send_email(faculty_email, subject, html_content)

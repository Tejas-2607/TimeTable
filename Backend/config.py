import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    # Trigger a connection check
    client.admin.command('ping')
except Exception as e:
    print(f"\n[CRITICAL ERROR] Failed to connect to MongoDB: {e}")
    print("If you see a DNS SERVFAIL error, try:")
    print("1. Restarting your network or DNS resolver (e.g., sudo systemctl restart systemd-resolved)")
    print("2. Changing your DNS servers to 8.8.8.8 or 1.1.1.1")
    print("3. Checking if your MongoDB Atlas IP Whitelist includes your current IP.\n")
    # For now, we still assign client/db to avoid downstream NameErrors, 
    # but the app will likely fail during first query.
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

# Flask-Mail Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

# APScheduler Configuration
SCHEDULER_API_ENABLED = True

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key_here')

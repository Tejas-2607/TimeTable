#!/usr/bin/env python3
from config import db
from werkzeug.security import generate_password_hash
from bson import ObjectId
from datetime import datetime

COL = db['faculty']

ADMIN_ID = ObjectId("69f6ef5d372034b7b126136c")
ADMIN_EMAIL = "admin@college.edu"
ADMIN_PASSWORD = "admin123"

ADMIN_DOC = {
    "_id": ADMIN_ID,
    "name": "System Administrator",
    "short_name": "ADMIN",
    "email": ADMIN_EMAIL.lower(),
    "role": "ADMIN",
    "created_at": datetime.fromisoformat("2026-05-03T06:46:53.735+00:00"),
}


def seed_admin():
    existing = COL.find_one({"$or": [{"_id": ADMIN_ID}, {"email": ADMIN_EMAIL.lower()}]})
    hashed = generate_password_hash(ADMIN_PASSWORD)

    if existing:
        print("Admin already exists — updating password and metadata.")
        COL.update_one(
            {"_id": existing["_id"]},
            {"$set": {"password": hashed, "name": ADMIN_DOC["name"], "short_name": ADMIN_DOC["short_name"], "role": ADMIN_DOC["role"], "created_at": ADMIN_DOC["created_at"]}}
        )
        print("Admin record updated.")
    else:
        admin = ADMIN_DOC.copy()
        admin["password"] = hashed
        COL.insert_one(admin)
        print("Admin user inserted.")


if __name__ == '__main__':
    seed_admin()

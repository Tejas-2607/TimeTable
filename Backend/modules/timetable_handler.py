from flask import jsonify, request
from bson import ObjectId
from config import db
import logging

# Collection reference
master_lab_timetable_collection = db['master_lab_timetable']

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_master_practical_timetable(data=None):
    """
    Fetch master practical timetables from the database.
    Supports optional filters for year and semester.

    Example Request Body:
    {
        "year": "SY",
        "sem": "1"
    }

    Example Response:
    {
        "timetables": [
            {
                "_id": "652b4a3f...",
                "lab_name": "DBMS Lab",
                "year": "SY",
                "semester": "1",
                "schedule": { "Monday": {...}, ... },
                "generated_at": "2025-10-29T12:30:00",
                "total_assignments": 12
            },
            ...
        ]
    }
    """
    try:
        query = {}
        if data:
            year = data.get("year")
            semester = data.get("sem")
            if year:
                query["year"] = year
            if semester:
                query["semester"] = semester

        timetables = list(master_lab_timetable_collection.find(query))

        # Convert ObjectIds and datetime to strings
        for t in timetables:
            t["_id"] = str(t["_id"])
            if "generated_at" in t and t["generated_at"]:
                t["generated_at"] = t["generated_at"].isoformat()

        logger.info(f"Fetched {len(timetables)} timetables from database.")
        return jsonify({"timetables": timetables}), 200

    except Exception as e:
        logger.error(f"Error fetching master timetable: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

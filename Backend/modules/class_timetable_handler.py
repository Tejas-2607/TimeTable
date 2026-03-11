# class_timetable_handler.py
"""
Converts Master Practical Timetable into individual Class Timetables
Each class (SY-A, SY-B, TY-A, etc.) gets its own timetable
"""

from flask import jsonify
from config import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Database collections
master_lab_timetable_collection = db['master_lab_timetable']
class_timetable_collection = db['class_timetable']
class_structure_collection = db['class_structure']

# Time slots
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
TIME_SLOTS = ['10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:20']


def generate_class_timetables():
    """
    Generate individual class timetables from master practical timetable.
    
    Process:
    1. Get all master practical sessions
    2. Group by class-division (SY-A, SY-B, TY-A, etc.)
    3. Create timetable structure for each class
    4. Place practical sessions in appropriate slots
    5. Save to database
    
    Returns: Success/failure status
    """
    try:
        logger.info("Starting class timetable generation...")
        
        # Clear existing class timetables
        deleted = class_timetable_collection.delete_many({}).deleted_count
        logger.info(f"Deleted {deleted} existing class timetables")
        
        # Get master practical timetable
        master_sessions = list(master_lab_timetable_collection.find({}))
        if not master_sessions:
            logger.warning("No master timetable found!")
            return {'success': False, 'error': 'Master timetable not found'}
        
        # Collect all sessions by class-division
        # Structure: {(class, division): [(day, slot, session), ...]}
        class_sessions = {}
        
        for lab_doc in master_sessions:
            lab_name = lab_doc.get('lab_name', 'Unknown')
            schedule = lab_doc.get('schedule', {})
            
            # Iterate through each day and slot
            for day in DAYS:
                day_schedule = schedule.get(day, {})
                
                for slot, sessions in day_schedule.items():
                    if not sessions:  # Empty slot
                        continue
                    
                    # Each session is a practical class
                    for session in sessions:
                        class_name = session.get('class')  # SY, TY, BE
                        division = session.get('division')  # A, B, C
                        
                        if not class_name or not division:
                            continue
                        
                        key = (class_name, division)
                        
                        if key not in class_sessions:
                            class_sessions[key] = []
                        
                        class_sessions[key].append({
                            'day': day,
                            'slot': slot,
                            'lab': lab_name,
                            'subject': session.get('subject'),
                            'subject_full': session.get('subject_full'),
                            'batch': session.get('batch'),
                            'faculty': session.get('faculty'),
                            'faculty_id': session.get('faculty_id')
                        })
        
        logger.info(f"Found {len(class_sessions)} classes to schedule")
        
        # Get class structure to know divisions and batches
        class_structure = class_structure_collection.find_one({})
        if not class_structure:
            logger.warning("No class structure found!")
            return {'success': False, 'error': 'Class structure not found'}
        
        # Create timetable for each class
        timetables_created = 0
        
        for (class_name, division), sessions in class_sessions.items():
            # Create empty timetable structure
            timetable = {
                'class': class_name,
                'division': division,
                'class_key': f"{class_name}-{division}",
                'schedule': {}
            }
            
            # Initialize all days and time slots as empty
            for day in DAYS:
                timetable['schedule'][day] = {}
                for slot in TIME_SLOTS:
                    timetable['schedule'][day][slot] = []
            
            # Fill in the practical sessions
            for session in sessions:
                day = session['day']
                slot = session['slot']
                
                # Create session entry (without filling subjects yet)
                session_entry = {
                    'batch': session['batch'],
                    'subject': session['subject'],
                    'subject_full': session['subject_full'],
                    'faculty': session['faculty'],
                    'faculty_id': session['faculty_id'],
                    'lab': session['lab'],
                    'type': 'practical'
                }
                
                # Add to the slot
                if day in timetable['schedule'] and slot in timetable['schedule'][day]:
                    timetable['schedule'][day][slot].append(session_entry)
            
            # Add metadata
            timetable['generated_at'] = datetime.now()
            timetable['total_practicals'] = len(sessions)
            
            # Save to database
            result = class_timetable_collection.insert_one(timetable)
            timetables_created += 1
            
            logger.info(f"Created timetable for {class_name}-{division} (ID: {result.inserted_id})")
        
        logger.info(f"✅ Successfully created {timetables_created} class timetables")
        
        return {
            'success': True,
            'message': f'Successfully generated {timetables_created} class timetables',
            'timetables_created': timetables_created
        }
        
    except Exception as e:
        logger.error(f"Error generating class timetables: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def get_class_timetable(class_name, division):
    """
    Fetch timetable for a specific class-division.
    
    Args:
        class_name: 'SY', 'TY', or 'BE'
        division: 'A', 'B', 'C', etc.
    
    Returns:
        Timetable JSON or error
    """
    try:
        if not class_name or not division:
            return jsonify({'error': 'Missing class_name or division'}), 400
        
        class_name = class_name.upper()
        division = division.upper()
        
        # Find timetable
        timetable = class_timetable_collection.find_one({
            'class': class_name,
            'division': division
        })
        
        if not timetable:
            return jsonify({
                'error': f'No timetable found for {class_name}-{division}'
            }), 404
        
        # Convert ObjectId to string
        timetable['_id'] = str(timetable['_id'])
        if 'generated_at' in timetable:
            timetable['generated_at'] = timetable['generated_at'].isoformat()
        
        return jsonify(timetable), 200
        
    except Exception as e:
        logger.error(f"Error fetching class timetable: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def get_all_class_timetables():
    """
    Fetch all class timetables.
    
    Returns:
        List of all class timetables
    """
    try:
        timetables = list(class_timetable_collection.find({}))
        
        # Convert ObjectIds to strings
        for t in timetables:
            t['_id'] = str(t['_id'])
            if 'generated_at' in t:
                t['generated_at'] = t['generated_at'].isoformat()
        
        return jsonify({
            'total': len(timetables),
            'timetables': timetables
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching all class timetables: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def get_class_timetable_summary(class_name, division):
    """
    Get a summary of a class timetable (shows which slots have practicals).
    
    Example output:
    {
        'class': 'SY',
        'division': 'A',
        'Monday': {
            '11:15': ['DS', 'CG', 'OOPJ'],
            '14:15': [],
            ...
        }
    }
    """
    try:
        if not class_name or not division:
            return jsonify({'error': 'Missing class_name or division'}), 400
        
        class_name = class_name.upper()
        division = division.upper()
        
        # Find timetable
        timetable = class_timetable_collection.find_one({
            'class': class_name,
            'division': division
        })
        
        if not timetable:
            return jsonify({
                'error': f'No timetable found for {class_name}-{division}'
            }), 404
        
        # Create summary
        summary = {
            'class': class_name,
            'division': division,
            'schedule': {}
        }
        
        # Extract subjects for each slot
        for day in DAYS:
            summary['schedule'][day] = {}
            day_schedule = timetable.get('schedule', {}).get(day, {})
            
            for slot in TIME_SLOTS:
                sessions = day_schedule.get(slot, [])
                subjects = [s.get('subject') for s in sessions]
                summary['schedule'][day][slot] = subjects
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error getting class timetable summary: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
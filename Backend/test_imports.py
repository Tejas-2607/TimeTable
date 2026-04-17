try:
    import flask
    import flask_cors
    import pymongo
    import dotenv
    print("All backend libraries imported successfully!")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)

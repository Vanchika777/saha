import os
from pymongo import MongoClient
import certifi

_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI is not configured in backend/.env")
        
        # Connect to MongoDB Atlas using certifi SSL certificates
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        # Default database name 'saha_db'
        _db_instance = client.get_database("saha_db")
        
    return _db_instance
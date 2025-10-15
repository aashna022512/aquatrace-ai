#!/usr/bin/env python3
"""
Test MongoDB Atlas connection for AquaTrace AI
Run this to verify your MongoDB setup is working
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    try:
        print("🔄 Testing MongoDB Atlas connection...")
        
        # Get connection details
        mongodb_uri = os.getenv('MONGODB_URI')
        db_name = os.getenv('MONGODB_DB_NAME')
        
        if not mongodb_uri:
            print("❌ MONGODB_URI not found in .env file")
            return False
            
        if not db_name:
            print("❌ MONGODB_DB_NAME not found in .env file")
            return False
            
        print(f"🌐 Cluster: Cluster0")
        print(f"📡 Database: {db_name}")
        
        # Create MongoDB client
        client = MongoClient(mongodb_uri)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database
        db = client[db_name]
        print(f"✅ Database '{db_name}' is ready inside Cluster0!")
        
        # Test collections access
        collections = ['users', 'uploads', 'global_stats']
        for collection_name in collections:
            collection = db[collection_name]
            count = collection.count_documents({})
            print(f"📊 Collection '{collection_name}': {count} documents")
        
        print("\n🎉 MongoDB Atlas setup is working perfectly!")
        print("🚀 Ready to migrate from SQLite to MongoDB!")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your .env file has the correct MONGODB_URI")
        print("2. Verify your MongoDB Atlas cluster is running")
        print("3. Check your network access settings in Atlas")
        return False

if __name__ == "__main__":
    test_mongodb_connection()

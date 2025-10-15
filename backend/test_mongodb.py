#!/usr/bin/env python3
"""
Test MongoDB Atlas Connection
"""

import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_public_ip():
    """Get your public IP address"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return "Unable to get IP"

def test_mongodb_connection():
    """Test MongoDB Atlas connection step by step"""
    print("🧪 MongoDB Atlas Connection Test")
    print("=" * 50)
    
    # Step 1: Check environment variables
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = os.getenv('MONGODB_DB_NAME', 'aquatrace_db')
    
    print(f"📋 Database Name: {DATABASE_NAME}")
    print(f"🔗 Connection URI: {MONGODB_URI[:50]}..." if MONGODB_URI else "❌ No URI found")
    print(f"🌐 Your Public IP: {get_public_ip()}")
    print()
    
    if not MONGODB_URI:
        print("❌ MONGODB_URI not found in .env file")
        return False
    
    # Step 2: Test connection
    try:
        print("🔗 Attempting to connect to MongoDB Atlas...")
        
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=15000,  # 15 seconds
            connectTimeoutMS=15000,
            socketTimeoutMS=15000
        )
        
        # Test ping
        print("📡 Testing connection with ping...")
        result = client.admin.command('ping')
        print(f"✅ Ping successful: {result}")
        
        # Test database access
        db = client[DATABASE_NAME]
        print(f"📂 Accessing database: {DATABASE_NAME}")
        
        # Test collection operations
        test_collection = db.test_connection
        
        # Insert test document
        print("📝 Testing write operation...")
        insert_result = test_collection.insert_one({"test": "connection", "timestamp": "2025-01-19"})
        print(f"✅ Insert successful: {insert_result.inserted_id}")
        
        # Read test document
        print("📖 Testing read operation...")
        doc = test_collection.find_one({"test": "connection"})
        print(f"✅ Read successful: {doc}")
        
        # Delete test document
        print("🗑️ Cleaning up test document...")
        delete_result = test_collection.delete_one({"test": "connection"})
        print(f"✅ Delete successful: {delete_result.deleted_count} document(s)")
        
        print("\n🎉 MongoDB Atlas connection is working perfectly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if your IP is whitelisted in MongoDB Atlas")
        print("2. Go to MongoDB Atlas → Network Access → Add IP Address")
        print(f"3. Add your IP: {get_public_ip()}")
        print("4. Or add 0.0.0.0/0 for all IPs (less secure)")
        print("5. Check if cluster is running (not paused)")
        print("6. Verify username/password in connection string")
        return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    
    if success:
        print("\n✅ Your MongoDB Atlas is ready!")
        print("💡 You can now run your Flask app: python app.py")
    else:
        print("\n❌ Please fix the MongoDB Atlas connection first")
        print("💡 Follow the troubleshooting steps above")

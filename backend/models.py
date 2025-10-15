from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
def connect_to_mongodb():
    try:
        # MongoDB Atlas connection with proper settings
        MONGODB_URI = os.getenv('MONGODB_URI')
        DATABASE_NAME = os.getenv('MONGODB_DB_NAME', 'aquatrace_db')
        
        print(f"🔗 Connecting to MongoDB Atlas...")
        
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,  # 10 seconds
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=10,
            retryWrites=True,
            w='majority'
        )
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB Atlas connected successfully!")
        
        db = client[DATABASE_NAME]
        
        return db
        
    except Exception as e:
        print(f"❌ MongoDB Atlas connection failed: {e}")
        print("🔧 Troubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Verify MongoDB Atlas cluster is running")
        print("3. Check IP whitelist in MongoDB Atlas")
        print("4. Verify username/password in connection string")
        raise e  # Re-raise the error to stop execution

# Connect to MongoDB
db = connect_to_mongodb()

if db is not None:
    # Collections
    users_collection = db.users
    uploads_collection = db.uploads
    global_stats_collection = db.global_stats

    class User:
        def __init__(self, username, email, password=None, bio=None, firebase_uid=None, _id=None, created_at=None):
            self._id = _id or ObjectId()
            self.username = username
            self.email = email
            self.password_hash = generate_password_hash(password) if password else None
            self.firebase_uid = firebase_uid
            self.bio = bio
            self.created_at = created_at or datetime.utcnow()
            self._is_authenticated = False
            self._is_active = True

        @property
        def is_authenticated(self):
            return self._is_authenticated
            
        @property
        def is_active(self):
            return self._is_active
            
        @property
        def is_anonymous(self):
            return False
            
        def get_id(self):
            return str(self._id)
        
        def to_dict(self):
            return {
                '_id': self._id,
                'username': self.username,
                'email': self.email,
                'password_hash': self.password_hash,
                'firebase_uid': self.firebase_uid,
                'bio': self.bio,
                'created_at': self.created_at
            }
        
        @staticmethod
        def from_dict(data):
            if not data:
                return None
            user = User(
                username=data['username'],
                email=data['email'],
                bio=data.get('bio'),
                firebase_uid=data.get('firebase_uid'),
                _id=data.get('_id'),
                created_at=data.get('created_at')
            )
            user.password_hash = data.get('password_hash')
            user._is_authenticated = True
            user._is_active = True
            return user
        
        def save(self):
            """Save user to MongoDB"""
            result = users_collection.insert_one(self.to_dict())
            self._id = result.inserted_id
            return self
        
        def update(self, **kwargs):
            """Update user in MongoDB"""
            update_data = {}
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    update_data[key] = value
            
            if update_data:
                users_collection.update_one({'_id': self._id}, {'$set': update_data})
            return self
        
        @staticmethod
        def find_by_username(username):
            """Find user by username"""
            user_data = users_collection.find_one({'username': username})
            return User.from_dict(user_data) if user_data else None
        
        @staticmethod
        def find_by_email(email):
            """Find user by email"""
            user_data = users_collection.find_one({'email': email})
            return User.from_dict(user_data) if user_data else None

        @staticmethod
        def find_by_firebase_uid(firebase_uid):
            """Find user by Firebase UID"""
            user_data = users_collection.find_one({'firebase_uid': firebase_uid})
            return User.from_dict(user_data) if user_data else None
        
        @staticmethod
        def find_by_id(user_id):
            """Find user by ID"""
            try:
                if not user_id:
                    return None
                if isinstance(user_id, str):
                    # Check if it's a valid ObjectId string
                    if not ObjectId.is_valid(user_id):
                        return None
                    user_id = ObjectId(user_id)
                elif not isinstance(user_id, ObjectId):
                    return None
                
                user_data = users_collection.find_one({'_id': user_id})
                return User.from_dict(user_data) if user_data else None
            except Exception as e:
                print(f"Error finding user by ID: {e}")
                return None
        
        def check_password(self, password):
            """Check if password matches"""
            return check_password_hash(self.password_hash, password)
        
        @staticmethod
        def count():
            """Count total users"""
            return users_collection.count_documents({})
    
    class Upload:
        def __init__(self, filename, species_name, confidence, user_id, latitude=None, longitude=None, _id=None, upload_date=None):
            self._id = _id or ObjectId()
            self.filename = filename
            self.species_name = species_name
            self.confidence = confidence
            self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            self.latitude = latitude
            self.longitude = longitude
            self.upload_date = upload_date or datetime.utcnow()
        
        def to_dict(self):
            return {
                '_id': self._id,
                'filename': self.filename,
                'species_name': self.species_name,
                'confidence': self.confidence,
                'user_id': self.user_id,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'upload_date': self.upload_date
            }
        
        @staticmethod
        def from_dict(data):
            return Upload(
                filename=data['filename'],
                species_name=data['species_name'],
                confidence=data['confidence'],
                user_id=data['user_id'],
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                _id=data.get('_id'),
                upload_date=data.get('upload_date')
            )
        
        def save(self):
            """Save upload to MongoDB"""
            result = uploads_collection.insert_one(self.to_dict())
            self._id = result.inserted_id
            return self

        @classmethod
        def find(cls, query=None):
            """Find uploads in MongoDB"""
            if query is None:
                query = {}
            uploads_data = uploads_collection.find(query)
            return [cls.from_dict(data) for data in uploads_data]

        @staticmethod
        def find_by_species(species_name):
            """Find uploads by species name"""
            uploads_data = uploads_collection.find({'species_name': species_name})
            return [Upload.from_dict(data) for data in uploads_data]
        
        @staticmethod
        def find_by_user_id(user_id):
            """Find uploads by user ID"""
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            uploads_data = uploads_collection.find({'user_id': user_id}).sort('upload_date', -1)
            return [Upload.from_dict(upload) for upload in uploads_data]
        
        @staticmethod
        def count():
            """Count total uploads"""
            return uploads_collection.count_documents({})
        
        @staticmethod
        def get_unique_species():
            """Get unique species names"""
            return uploads_collection.distinct('species_name', {'species_name': {'$ne': None}})
    
    class GlobalStats:
        def __init__(self, total_identifications=0, total_users=0, total_species=0, _id=None, last_updated=None):
            self._id = _id or ObjectId()
            self.total_identifications = total_identifications
            self.total_users = total_users
            self.total_species = total_species
            self.last_updated = last_updated or datetime.utcnow()
        
        def to_dict(self):
            return {
                '_id': self._id,
                'total_identifications': self.total_identifications,
                'total_users': self.total_users,
                'total_species': self.total_species,
                'last_updated': self.last_updated
            }
        
        @staticmethod
        def from_dict(data):
            return GlobalStats(
                total_identifications=data['total_identifications'],
                total_users=data['total_users'],
                total_species=data['total_species'],
                _id=data.get('_id'),
                last_updated=data.get('last_updated')
            )
        
        def save(self):
            """Save or update global stats"""
            global_stats_collection.replace_one(
                {},
                self.to_dict(),
                upsert=True
            )
            return self
        
        @staticmethod
        def get_current():
            """Get current global stats"""
            stats_data = global_stats_collection.find_one()
            return GlobalStats.from_dict(stats_data) if stats_data else GlobalStats()
        
        @staticmethod
        def find_one():
            """Find one stats document"""
            stats_data = global_stats_collection.find_one()
            return GlobalStats.from_dict(stats_data) if stats_data else None

    # Initialize indexes for better performance
    def create_indexes():
        """Create database indexes for better performance"""
        try:
            users_collection.create_index('username', unique=True)
            users_collection.create_index('email', unique=True)
            uploads_collection.create_index('user_id')
            uploads_collection.create_index('upload_date')
            uploads_collection.create_index('species_name')
            print("✅ MongoDB indexes created successfully!")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")

    # Call this when the module is imported
    create_indexes()

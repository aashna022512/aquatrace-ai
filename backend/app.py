from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from PIL import Image, ImageEnhance
import io
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.resnet_v2 import ResNet50V2, preprocess_input as resnet_preprocess_input
import requests
from bson import ObjectId
import firebase_admin
from firebase_admin import credentials, auth
import os

# Import MongoDB models instead of SQLAlchemy
from models import User, Upload, GlobalStats

# Import Vision API fallback
try:
    from vision_api_fallback import identify_marine_species_with_vision_api
    VISION_API_AVAILABLE = True
    print("✅ Google Cloud Vision API fallback loaded successfully!")
except ImportError as e:
    VISION_API_AVAILABLE = False
    print(f"⚠️ Vision API fallback not available: {e}")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY')
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
MAPS_API_KEY = os.getenv('MAPS_API')  # Google Maps API key

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login with session protection
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'  # Enable strong session protection

# Initialize Firebase Admin SDK
if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
    try:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized successfully")
    except Exception as e:
        print(f"❌ Firebase Admin SDK initialization failed: {e}")
        firebase_admin.initialize_app()
else:
    # Try to load marine.json explicitly if env var not set
    try:
        cred_path = os.path.join(os.path.dirname(__file__), 'marine.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized successfully with marine.json")
        else:
            print("⚠️ Firebase credentials not found, initializing without credentials")
            firebase_admin.initialize_app()
    except ValueError:
        print("Firebase app already initialized")

@login_manager.user_loader
def load_user(user_id):
    try:
        if not user_id:
            return None
        user = User.find_by_id(user_id)
        if user:
            user._is_authenticated = True
            user._is_active = True
        return user
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Load the .h5 model
MODEL_DIR = 'model'  # Model is in backend/model/ folder
model_path = os.path.join(os.path.dirname(__file__), MODEL_DIR, 'sea_animal_model.h5')
model = None

def load_my_model():
    """Load the sea animal model directly"""
    try:
        print(" Loading sea animal model...")
        
        # Define the model architecture first
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(224, 224, 3),
            include_top=False,
            weights='imagenet'
        )
        base_model.trainable = False

        model = tf.keras.models.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(9, activation='softmax')  # 9 sea animal classes
        ])
        
        # Load the weights
        model.load_weights(model_path)
        
        print(" Model loaded successfully!")
        print(f" Input shape: {model.input_shape}")
        print(f" Output shape: {model.output_shape}")
        print(f" Total parameters: {model.count_params():,}")
        
        return model
        
    except Exception as e:
        print(f" Error loading your model: {e}")
        return None

# Load the model on startup
try:
    print(" Initializing model...")
    model = load_my_model()
    
    if model is not None:
        print(" MODEL LOADED SUCCESSFULLY! Ready for predictions!")
    else:
        print(" Model loading failed")
        
except Exception as e:
    print(f" Critical error: {e}")
    model = None

# Test MongoDB connection on startup
try:
    print(" Testing MongoDB connection...")
    test_count = User.count()
    print(f" MongoDB connected! Current users: {test_count}")
except Exception as e:
    print(f" MongoDB connection failed: {e}")

# OAuth 2 client setup
google_client = None
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    try:
        google_client = WebApplicationClient(GOOGLE_CLIENT_ID)
        print(" Google OAuth client initialized successfully")
    except Exception as e:
        print(f" Error initializing Google OAuth client: {e}")
        google_client = None
else:
    print(" Google OAuth credentials not found in environment variables")



UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to view this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def update_global_stats():
    """Update global statistics"""
    try:
        stats = GlobalStats.find_one()
        if not stats:
            stats = GlobalStats()

        # Get real-time statistics
        total_identifications = Upload.count()
        total_users = User.count()
        # Pass an empty dictionary to the find() method to get all documents
        all_uploads = Upload.find({})
        total_species = len(set(upload.species_name for upload in all_uploads))

        stats.total_identifications = total_identifications
        stats.total_users = total_users
        stats.total_species = total_species
        stats.last_updated = datetime.utcnow()

        stats.save()
        return stats
    except Exception as e:
        print(f"Error updating global stats: {e}")
        return None

SPECIES_NAMES = [
    'Coral',            # 0
    'Fish',             # 1
    'Jelly Fish',       # 2
    'Lobster',          # 3
    'Penguin',          # 4
    'Seal',             # 5
    'Sharks',           # 6
    'Squid',            # 7
    'Turtle'            # 8
]

def get_animal_details(animal_name):
    """Get detailed information about marine species"""
    animal_database = {
        "angelfish": {
            "scientific_name": "Pomacanthidae",
            "facts": "Angelfish are colorful marine fish known for their distinctive flat, disc-shaped bodies and vibrant patterns.",
            "endangered_status": "Least Concern to Vulnerable",
            "fun_fact": "Angelfish can change their colors and patterns as they mature!",
            "habitat": "Coral reefs in tropical waters",
            "diet": "Algae, small invertebrates, and sponges",
            "size": "7-60cm depending on species",
            "threats": "Coral reef destruction, aquarium trade",
            "population_trend": "Stable to declining"
        },
        "clownfish": {
            "scientific_name": "Amphiprioninae",
            "facts": "Clownfish live in symbiosis with sea anemones, protected by a special mucus coating.",
            "endangered_status": "Least Concern",
            "fun_fact": "All clownfish are born male and can change to female when needed!",
            "habitat": "Coral reefs and anemones in Indo-Pacific",
            "diet": "Algae, zooplankton, and anemone tentacles",
            "size": "10-18cm",
            "threats": "Coral bleaching, aquarium trade",
            "population_trend": "Stable"
        },
        "sharks": {
            "name": "Sharks",
            "scientific_name": "Selachimorpha",
            "facts": "Sharks are apex predators with cartilaginous skeletons and multiple rows of teeth.",
            "endangered_status": "Many species threatened",
            "fun_fact": "Sharks have existed for over 400 million years!",
            "habitat": "All ocean environments worldwide",
            "diet": "Fish, marine mammals, plankton",
            "size": "20cm to 12m depending on species",
            "threats": "Overfishing, finning, bycatch",
            "population_trend": "Declining globally"
        },
        "sea turtle": {
            "name": "Sea Turtle",
            "scientific_name": "Chelonioidea",
            "facts": "Sea turtles are ancient marine reptiles that navigate using Earth's magnetic field.",
            "endangered_status": "Most species endangered",
            "fun_fact": "Sea turtles return to the same beach where they were born to nest!",
            "habitat": "Oceans worldwide, nesting on beaches",
            "diet": "Jellyfish, seagrass, algae, crustaceans",
            "size": "60cm to 2m shell length",
            "threats": "Plastic pollution, fishing nets, beach development",
            "population_trend": "Declining globally"
        },
        "Dolphin": {
            "name": "Dolphin",
            "scientific_name": "Delphinidae",
            "facts": "Dolphins are highly intelligent marine mammals with complex social structures.",
            "endangered_status": "Varies by species",
            "fun_fact": "Dolphins have names for each other using unique whistle signatures!",
            "habitat": "Oceans and some rivers worldwide",
            "diet": "Fish, squid, and crustaceans",
            "size": "1.2-9m depending on species",
            "threats": "Fishing nets, pollution, boat strikes",
            "population_trend": "Varies by species"
        },
        "octopus": {
            "name": "Octopus",
            "scientific_name": "Octopoda",
            "facts": "Octopuses are intelligent cephalopods with eight arms and three hearts.",
            "endangered_status": "Most species least concern",
            "fun_fact": "Octopuses can change color and texture instantly to camouflage!",
            "habitat": "Ocean floors worldwide",
            "diet": "Crabs, shrimp, fish, and mollusks",
            "size": "5cm to 9m arm span",
            "threats": "Overfishing, habitat destruction",
            "population_trend": "Generally stable"
        },
        "jellyfish": {
            "name": "Jellyfish",
            "scientific_name": "Cnidaria",
            "facts": "Jellyfish are ancient creatures composed of 95% water with no brain or heart.",
            "endangered_status": "Most species stable",
            "fun_fact": "Some jellyfish species are immortal and can reverse their aging process!",
            "habitat": "All ocean environments",
            "diet": "Plankton, small fish, and other jellyfish",
            "size": "1mm to 2m bell diameter",
            "threats": "Climate change, pollution",
            "population_trend": "Many species increasing"
        },
        "seahorse": {
            "name": "Seahorse",
            "scientific_name": "Hippocampus",
            "facts": "Seahorses are unique fish where males carry and give birth to the young.",
            "endangered_status": "Many species vulnerable",
            "fun_fact": "Seahorses mate for life and perform elaborate courtship dances!",
            "habitat": "Shallow coastal waters with seagrass",
            "diet": "Small crustaceans and plankton",
            "size": "1.5-35cm",
            "threats": "Habitat loss, traditional medicine trade",
            "population_trend": "Declining"
        },
        "pufferfish": {
            "name": "Pufferfish",
            "scientific_name": "Tetraodontidae",
            "facts": "Pufferfish can inflate their bodies and contain potent neurotoxins.",
            "endangered_status": "Most species stable",
            "fun_fact": "Some pufferfish create intricate sand circles to attract mates!",
            "habitat": "Tropical and subtropical waters",
            "diet": "Algae, invertebrates, and small fish",
            "size": "2.5cm to 1.2m",
            "threats": "Overfishing, habitat destruction",
            "population_trend": "Generally stable"
        },
        "ray": {
            "name": "Rays",
            "scientific_name": "Batoidea",
            "facts": "Rays are flattened cartilaginous fish related to sharks.",
            "endangered_status": "Many species threatened",
            "fun_fact": "Manta rays have the largest brain-to-body ratio of any fish!",
            "habitat": "Ocean floors and open water",
            "diet": "Plankton, small fish, mollusks",
            "size": "10cm to 9m wingspan",
            "threats": "Overfishing, bycatch, habitat loss",
            "population_trend": "Declining"
        },
        "clams": {
            "name": "Clams",
            "scientific_name": "Bivalvia",
            "facts": "Clams are filter-feeding marine bivalve mollusks that live in sand or mud.",
            "endangered_status": "Least Concern",
            "fun_fact": "The giant clam can live for over 100 years!",
            "habitat": "Benthic zones of oceans and freshwater",
            "diet": "Phytoplankton and organic particles",
            "size": "Up to 1.2m (giant clam)",
            "threats": "Over-harvesting, ocean acidification",
            "population_trend": "Stable"
        },
        "corals": {
            "name": "Corals",
            "scientific_name": "Anthozoa",
            "facts": "Corals are marine invertebrates that live in colonies and form the foundation of coral reefs.",
            "endangered_status": "Many species are threatened",
            "fun_fact": "Corals are actually animals, not plants!",
            "habitat": "Tropical and subtropical waters",
            "diet": "Plankton and photosynthesis from algae",
            "size": "Varies widely",
            "threats": "Coral bleaching, climate change, pollution",
            "population_trend": "Declining"
        },
        "crabs": {
            "name": "Crabs",
            "scientific_name": "Brachyura",
            "facts": "Crabs are crustaceans with a thick exoskeleton and a single pair of pincers.",
            "endangered_status": "Most species least concern",
            "fun_fact": "Crabs can walk sideways, but some species can also walk forward and backward!",
            "habitat": "Coastal waters, tide pools, and deep sea",
            "diet": "Algae, mollusks, worms, other crustaceans",
            "size": "1cm to 4m leg span (Japanese spider crab)",
            "threats": "Overfishing, habitat destruction",
            "population_trend": "Generally stable"
        },
        "eel": {
            "name": "Eel",
            "scientific_name": "Anguilliformes",
            "facts": "Eels are long, slender fish that can grow to be several meters long.",
            "endangered_status": "Varies by species",
            "fun_fact": "Some eels can produce electricity to stun their prey!",
            "habitat": "Coastal waters, coral reefs, deep sea",
            "diet": "Fish, crustaceans, and other invertebrates",
            "size": "10cm to 4m",
            "threats": "Overfishing, habitat loss",
            "population_trend": "Varies by species"
        },
        "fish": {
            "name": "Fish",
            "scientific_name": "Vertebrata",
            "facts": "Fish are aquatic vertebrates that have gills and fins. They are the most diverse group of vertebrates.",
            "endangered_status": "Varies widely by species",
            "fun_fact": "There are over 34,000 known species of fish!",
            "habitat": "All water environments",
            "diet": "Varies widely",
            "size": "Varies widely",
            "threats": "Overfishing, habitat destruction, pollution",
            "population_trend": "Varies widely"
        },
        "jelly fish": {
            "name": "Jellyfish",
            "scientific_name": "Cnidaria",
            "facts": "Jellyfish are ancient creatures composed of 95% water with no brain or heart.",
            "endangered_status": "Most species stable",
            "fun_fact": "Some jellyfish species are immortal and can reverse their aging process!",
            "habitat": "All ocean environments",
            "diet": "Plankton, small fish, and other jellyfish",
            "size": "1mm to 2m bell diameter",
            "threats": "Climate change, pollution",
            "population_trend": "Many species increasing"
        },
        "lobster": {
            "name": "Lobster",
            "scientific_name": "Nephropidae",
            "facts": "Lobsters are large marine crustaceans with a long body and muscular tail, and a pair of large claws.",
            "endangered_status": "Least Concern",
            "fun_fact": "Lobsters can live for over 50 years and grow indefinitely!",
            "habitat": "Ocean floors in temperate waters",
            "diet": "Fish, crustaceans, and mollusks",
            "size": "20-60cm",
            "threats": "Overfishing",
            "population_trend": "Stable"
        },
        "nudibranchs": {
            "name": "Nudibranchs",
            "scientific_name": "Nudibranchia",
            "facts": "Nudibranchs, or sea slugs, are shell-less marine gastropod mollusks known for their vibrant colors.",
            "endangered_status": "Not evaluated",
            "fun_fact": "Nudibranchs steal stinging cells from jellyfish and use them for their own defense!",
            "habitat": "Ocean floors worldwide",
            "diet": "Sponges, anemones, and other nudibranchs",
            "size": "5mm to 60cm",
            "threats": "Pollution, habitat loss",
            "population_trend": "Stable"
        },
        "otter": {
            "name": "Otter",
            "scientific_name": "Lutrinae",
            "facts": "Otters are carnivorous mammals found in both marine and freshwater environments.",
            "endangered_status": "Varies by species",
            "fun_fact": "Sea otters use rocks as tools to crack open shellfish!",
            "habitat": "Coastal waters and rivers worldwide",
            "diet": "Fish, crustaceans, and mollusks",
            "size": "60cm to 1.8m",
            "threats": "Habitat loss, pollution, hunting",
            "population_trend": "Varies by species"
        },
        "penguin": {
            "name": "Penguin",
            "scientific_name": "Spheniscidae",
            "facts": "Penguins are flightless birds that are highly adapted for life in the water.",
            "endangered_status": "Varies by species",
            "fun_fact": "Penguins can drink saltwater because they have a special gland to filter out the salt!",
            "habitat": "Southern Hemisphere oceans and coastlines",
            "diet": "Fish, squid, and krill",
            "size": "30cm to 1.2m",
            "threats": "Climate change, habitat loss, pollution",
            "population_trend": "Varies by species"
        },
        "puffers": {
            "name": "Pufferfish",
            "scientific_name": "Tetraodontidae",
            "facts": "Pufferfish can inflate their bodies and contain potent neurotoxins.",
            "endangered_status": "Most species stable",
            "fun_fact": "Some pufferfish create intricate sand circles to attract mates!",
            "habitat": "Tropical and subtropical waters",
            "diet": "Algae, invertebrates, and small fish",
            "size": "2.5cm to 1.2m",
            "threats": "Overfishing, habitat destruction",
            "population_trend": "Generally stable"
        },
        "sea rays": {
            "name": "Sea Rays",
            "scientific_name": "Batoidea",
            "facts": "Rays are flattened cartilaginous fish related to sharks.",
            "endangered_status": "Many species threatened",
            "fun_fact": "Manta rays have the largest brain-to-body ratio of any fish!",
            "habitat": "Ocean floors and open water",
            "diet": "Plankton, small fish, mollusks",
            "size": "10cm to 9m wingspan",
            "threats": "Overfishing, bycatch, habitat loss",
            "population_trend": "Declining"
        },
        "sea urchins": {
            "name": "Sea Urchins",
            "scientific_name": "Echinoidea",
            "facts": "Sea urchins are spiny, globular marine echinoderms that live in the seabed.",
            "endangered_status": "Most species stable",
            "fun_fact": "Sea urchins use their spines for defense, movement, and to trap food!",
            "habitat": "Ocean floors worldwide",
            "diet": "Algae, small invertebrates, and decaying matter",
            "size": "3-10cm diameter",
            "threats": "Over-harvesting, pollution",
            "population_trend": "Stable"
        },
        "seahorse": {
            "name": "Seahorse",
            "scientific_name": "Hippocampus",
            "facts": "Seahorses are unique fish where males carry and give birth to the young.",
            "endangered_status": "Many species vulnerable",
            "fun_fact": "Seahorses mate for life and perform elaborate courtship dances!",
            "habitat": "Shallow coastal waters with seagrass",
            "diet": "Small crustaceans and plankton",
            "size": "1.5-35cm",
            "threats": "Habitat loss, traditional medicine trade",
            "population_trend": "Declining"
        },
        "sea lion": {
            "name": "Sea Lion",
            "scientific_name": "Otariinae",
            "facts": "Sea lions are pinnipeds known for their external ear flaps, long front flippers, and the ability to walk on all fours on land.",
            "endangered_status": "Most species least concern",
            "fun_fact": "Sea lions can bark like dogs and have a very social nature!",
            "habitat": "Coastal waters and islands worldwide",
            "diet": "Fish, squid, and crustaceans",
            "size": "1.5-3m",
            "threats": "Fishing gear entanglement, habitat destruction",
            "population_trend": "Stable to declining"
        },
        "sharks": {
            "name": "Sharks",
            "scientific_name": "Selachimorpha",
            "facts": "Sharks are apex predators with cartilaginous skeletons and multiple rows of teeth.",
            "endangered_status": "Many species threatened",
            "fun_fact": "Sharks have existed for over 400 million years!",
            "habitat": "All ocean environments worldwide",
            "diet": "Fish, marine mammals, plankton",
            "size": "20cm to 12m depending on species",
            "threats": "Overfishing, finning, bycatch",
            "population_trend": "Declining globally"
        },
        "shrimp": {
            "name": "Shrimp",
            "scientific_name": "Pleocyemata",
            "facts": "Shrimp are small marine crustaceans that are an important food source for many marine animals.",
            "endangered_status": "Least Concern",
            "fun_fact": "Some shrimp species can snap their claws so fast it creates a sound louder than a gunshot!",
            "habitat": "All water environments",
            "diet": "Algae, organic particles, and small invertebrates",
            "size": "2-20cm",
            "threats": "Overfishing, habitat destruction",
            "population_trend": "Stable"
        },
        "squid": {
            "name": "Squid",
            "scientific_name": "Teuthida",
            "facts": "Squid are cephalopods known for their large eyes, eight arms, two tentacles, and the ability to squirt ink.",
            "endangered_status": "Least Concern",
            "fun_fact": "Some squid species can fly out of the water for short distances!",
            "habitat": "All ocean environments",
            "diet": "Fish, crustaceans, and other squid",
            "size": "5cm to 13m (giant squid)",
            "threats": "Overfishing",
            "population_trend": "Stable"
        },
        "starfish": {
            "name": "Starfish",
            "scientific_name": "Asteroidea",
            "facts": "Starfish are marine invertebrates with radial symmetry, typically having five arms.",
            "endangered_status": "Least Concern",
            "fun_fact": "Starfish can regenerate lost arms and sometimes even a whole new body!",
            "habitat": "Ocean floors worldwide",
            "diet": "Mollusks, crustaceans, and other invertebrates",
            "size": "2cm to 1m",
            "threats": "Habitat destruction, pollution",
            "population_trend": "Stable"
        },
        "turtle_tortoise": {
            "name": "Sea Turtle",
            "scientific_name": "Chelonioidea",
            "facts": "Sea turtles are ancient marine reptiles that navigate using Earth's magnetic field.",
            "endangered_status": "Most species endangered",
            "fun_fact": "Sea turtles return to the same beach where they were born to nest!",
            "habitat": "Oceans worldwide, nesting on beaches",
            "diet": "Jellyfish, seagrass, algae, crustaceans",
            "size": "60cm to 2m shell length",
            "threats": "Plastic pollution, fishing nets, beach development",
            "population_trend": "Declining globally"
        },
        "whale": {
            "name": "Whale",
            "scientific_name": "Cetacea",
            "facts": "Whales are large marine mammals known for their intelligence and complex communication.",
            "endangered_status": "Varies by species",
            "fun_fact": "Blue whales are the largest animals ever known to have existed!",
            "habitat": "All ocean environments worldwide",
            "diet": "Krill, plankton, fish, and squid",
            "size": "3m to 30m",
            "threats": "Whaling, noise pollution, climate change",
            "population_trend": "Varies by species"
        },
        "Fish": {
            "name": "Fish",
            "scientific_name": "Various",
            "facts": "This category covers a wide range of aquatic vertebrates.",
            "endangered_status": "Varies widely",
            "fun_fact": "There are over 34,000 known species of fish!",
            "habitat": "All water environments",
            "diet": "Varies widely",
            "size": "Varies widely",
            "threats": "Overfishing, habitat destruction, pollution",
            "population_trend": "Varies widely"
        },
        "Sea Lion": {
            "name": "Sea Lion",
            "scientific_name": "Otariinae",
            "facts": "Sea lions are pinnipeds known for their external ear flaps, long front flippers, and the ability to walk on all fours on land.",
            "endangered_status": "Most species least concern",
            "fun_fact": "Sea lions can bark like dogs and have a very social nature!",
            "habitat": "Coastal waters and islands worldwide",
            "diet": "Fish, squid, and crustaceans",
            "size": "1.5-3m",
            "threats": "Fishing gear entanglement, habitat destruction",
            "population_trend": "Stable to declining"
        },
        "Sea Rays": {
            "name": "Sea Rays",
            "scientific_name": "Batoidea",
            "facts": "Rays are flattened cartilaginous fish related to sharks.",
            "endangered_status": "Many species threatened",
            "fun_fact": "Manta rays have the largest brain-to-body ratio of any fish!",
            "habitat": "Ocean floors and open water",
            "diet": "Plankton, small fish, mollusks",
            "size": "10cm to 9m wingspan",
            "threats": "Overfishing, bycatch, habitat loss",
            "population_trend": "Declining"
        }
    }
    
    # Try to find a match in the database
    for key, details in animal_database.items():
        if key.lower().replace('_', ' ') == animal_name.lower().replace('_', ' '):
            # Return a copy to avoid accidental modification of the original dictionary
            result = details.copy()
            # If a 'name' key is not present, use the provided animal_name
            if 'name' not in result:
                result['name'] = animal_name
            return result
    
    # Return default marine species information
    return {
        "name": animal_name.replace('_', ' '),
        "scientific_name": "Unknown",
        "facts": f"This appears to be a {animal_name.replace('_', ' ')}, a marine species found in ocean environments.",
        "endangered_status": "Unknown",
        "fun_fact": "Marine ecosystems are incredibly diverse with unique adaptations!",
        "habitat": "Marine environments",
        "diet": "Varies by species",
        "size": "Varies by species",
        "threats": "Climate change, pollution, overfishing",
        "population_trend": "Unknown"
    }

# Initialize ResNet50V2 model on startup
print("Initializing model...")
if model:
    print("Model ready!")
else:
    print("Model failed to load!")

def identify_species_with_h5(image_path):
    """Strict sequence: try local H5 model, then Vision API fallback; if both fail, return None."""
    try:
        print(f" Processing: {image_path}")
        
        # PEHLE H5 MODEL TRY KARTE HAIN
        if model is not None:
            try:
                print(" H5 model se predict kar rahe hain...")
                
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img = img.resize((224, 224), Image.Resampling.LANCZOS)
                img_array = np.array(img, dtype=np.float32)
                img_array = np.expand_dims(img_array, axis=0)
                img_array = img_array / 255.0
                
                predictions = model.predict(img_array, verbose=0)
                confidence = float(np.max(predictions[0])) * 100
                predicted_class_index = np.argmax(predictions[0])
                
                if confidence > 85 and predicted_class_index < len(SPECIES_NAMES):
                    species_name = SPECIES_NAMES[predicted_class_index]
                    print(f" H5 success: {species_name} ({confidence:.1f}%)")
                    
                    animal_details = get_animal_details(species_name)
                    return {
                        "name": animal_details.get('name', species_name),
                        "scientific_name": animal_details.get('scientific_name', 'Unknown'),
                        "confidence": round(confidence, 1),
                        "facts": animal_details.get('facts', f"This is a {species_name}."),
                        "endangered_status": animal_details.get('endangered_status', 'Unknown'),
                        "fun_fact": animal_details.get('fun_fact', f"Cool fact about {species_name}!"),
                        "habitat": animal_details.get('habitat', 'Marine environment'),
                        "diet": animal_details.get('diet', 'Varies'),
                        "size": animal_details.get('size', 'Varies'),
                        "threats": animal_details.get('threats', 'Climate change'),
                        "population_trend": animal_details.get('population_trend', 'Unknown'),
                        "detection_method": "H5 Model"
                    }
                else:
                    print(f" Confidence below 85% ({confidence:.1f}%), falling back to Vision API...")
                    if VISION_API_AVAILABLE:
                        try:
                            return identify_marine_species_with_vision_api(image_path)
                        except Exception as vision_error:
                            print(f" Vision API error: {vision_error}")
                            raise
                    raise Exception(f"Low confidence: {confidence:.1f}% and Vision API not available")
                    
            except Exception as h5_error:
                print(f" H5 model fail: {h5_error}")
        
        # VISION API FALLBACK
        if VISION_API_AVAILABLE:
            try:
                print(" Vision API fallback use kar rahe hain...")
                result = identify_marine_species_with_vision_api(image_path)
                print(f" Vision API success: {result['name']}")
                return result
            except Exception as vision_error:
                print(f" Vision API bhi fail: {vision_error}")
        
        # Both failed -> return None (no user-facing error payload)
        return None
            
    except Exception as e:
        print(f" Critical error: {e}")
        return None

@app.route("/")
def index():
    # Pass the current_user object and authentication state explicitly
    is_authenticated = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
    username = current_user.username if is_authenticated else None
    return render_template("index.html", 
                         current_user=current_user,
                         is_authenticated=is_authenticated,
                         username=username)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.find_by_username(username):
            flash('Username already exists', 'error')
            return render_template("register.html")
        
        if User.find_by_email(email):
            flash('Email already registered', 'error')
            return render_template("register.html")
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        user.save()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Try to find user by username or email
        user = User.find_by_username(username)
        if not user:
            user = User.find_by_email(username)

        if user and user.check_password(password):
            # Set authentication flag
            user._is_authenticated = True

            # Log the user in and remember them
            login_user(user, remember=True)
            session['user_id'] = str(user._id)
            session['username'] = user.username

            # Flash a success message
            flash('Successfully logged in!', 'success')

            flash('Login successful!', 'success')

            # Get the page they were trying to access or go to dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page and next_page != '/' else redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password', 'error')

    return render_template("login.html")

@app.route("/firebase_login", methods=['POST'])
def firebase_login():
    """Handle Firebase authentication"""
    try:
        data = request.get_json()
        id_token = data.get('id_token')

        if not id_token:
            return jsonify({'success': False, 'message': 'ID token is required'}), 400

        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')

        # Check if user exists by firebase_uid
        user = User.find_by_firebase_uid(firebase_uid)

        if not user:
            # Check if user exists by email to avoid duplicate key error
            user = User.find_by_email(email)
        
        if not user:
            # Create new user if doesn't exist
            # Generate a unique username from email or name
            base_username = email.split('@')[0] if email else f"firebase_{firebase_uid[:8]}"
            username = base_username
            counter = 1
            while User.find_by_username(username):
                username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                username=username,
                email=email or f"{firebase_uid}@firebase.local",
                firebase_uid=firebase_uid
            )
            user.save()
            print(f"✅ Created new Firebase user: {username}")

        # Set authentication flag
        user._is_authenticated = True

        # Log the user in
        login_user(user, remember=True)
        session['user_id'] = str(user._id)
        session['username'] = user.username

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': str(user._id),
                'username': user.username,
                'email': user.email
            }
        })

    except auth.InvalidIdTokenError:
        return jsonify({'success': False, 'message': 'Invalid ID token'}), 401
    except auth.ExpiredIdTokenError:
        return jsonify({'success': False, 'message': 'ID token has expired'}), 401
    except auth.RevokedIdTokenError:
        return jsonify({'success': False, 'message': 'ID token has been revoked'}), 401
    except Exception as e:
        print(f"Firebase login error: {e}")
        return jsonify({'success': False, 'message': 'Authentication failed'}), 500

@app.route("/google_login")
def google_login():
    if not google_client or not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Google login is not configured. Please check OAuth credentials.', 'error')
        return redirect(url_for('login'))
    
    try:
        google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Use proper redirect URI
        redirect_uri = request.url_root.rstrip('/') + "/google_login/callback"
        
        request_uri = google_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        print(f"Google login error: {e}")
        flash('Google login failed. Please try again later.', 'error')
        return redirect(url_for('login'))

@app.route("/google_login/callback")
def google_callback():
    if not google_client:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('login'))
    
    try:
        code = request.args.get("code")
        if not code:
            flash('Authorization code not received from Google', 'error')
            return redirect(url_for('login'))
            
        google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Use proper redirect URI
        redirect_uri = request.url_root.rstrip('/') + "/google_login/callback"

        token_url, headers, body = google_client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=redirect_uri,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        if token_response.status_code != 200:
            print(f"Google token error: {token_response.text}")
            flash('Failed to get access token from Google', 'error')
            return redirect(url_for('login'))
            
        google_client.parse_request_body_response(token_response.text)
        
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = google_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if userinfo_response.status_code != 200:
            print(f"Google userinfo error: {userinfo_response.text}")
            flash('Failed to get user info from Google', 'error')
            return redirect(url_for('login'))

        user_info = userinfo_response.json()
        
        # Check if user exists
        user = User.find_by_email(user_info['email'])
        if not user:
            # Create new user with unique username
            base_username = user_info.get('name', 'google_user')
            
            # Check if username exists, make it unique
            counter = 1
            while User.find_by_username(base_username):
                base_username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                username=base_username,
                email=user_info['email'],
                password='oauth_google_temp'  # Temporary password for OAuth users
            )
            # Override with OAuth marker
            user.password_hash = 'oauth_google'
            user.save()
            print(f"✅ Created new Google user: {base_username}")
        else:
            print(f"✅ Existing Google user login: {user.username}")
        
        session['user_id'] = str(user._id)
        session['username'] = user.username
        login_user(user, remember=True)
        flash(f'Welcome, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"Google callback error: {e}")
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route("/conservation")
def conservation():
    try:
        # Get user data if logged in
        user_data = None
        if 'user_id' in session:
            user_data = User.find_by_id(ObjectId(session.get('user_id')))
            
        # Default stats
        stats = {
            'total_participants': 1250,
            'challenges_completed': 856,
            'species_protected': 127,
            'conservation_impact': 95
        }
        
        return render_template('conservation.html', user=user_data, stats=stats)
    except Exception as e:
        print(f"Error in conservation route: {e}")
        return redirect(url_for('index'))



@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_user._is_authenticated = False
        logout_user()
        flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    """Main prediction endpoint using Gemini Pro Vision - Returns JSON for API calls"""
    try:
        # Check if image file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400
        
        image_file = request.files['file']
        
        # Check if file is selected
        if image_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Check file extension
        if not allowed_file(image_file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, BMP, WEBP).',
                "traceback": "Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, BMP, WEBP)."
            }), 400
        
        # Secure filename and save
        filename = secure_filename(image_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        img_path = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(img_path)
        
        # Get current user
        user = User.find_by_id(session['user_id'])
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 401
        
        # Identify animal using .h5 model (with Vision fallback)
        animal_data = identify_species_with_h5(img_path)

        if animal_data is None:
            # Return success with no prediction; do not save or flash any error
            return jsonify({
                'status': 'success',
                'prediction': None,
                'user': {
                    'id': str(user.id),
                    'username': user.username
                }
            })

        # Save prediction to database
        upload = Upload(
            filename=filename,
            species_name=animal_data['name'],
            confidence=animal_data['confidence'],
            user_id=ObjectId(session['user_id'])
        )
        upload.save()
        
        # Return JSON response
        return jsonify({
            'status': 'success',
            'prediction': {
                'name': animal_data['name'],
                'scientific_name': animal_data.get('scientific_name', 'Unknown'),
                'confidence': animal_data['confidence'],
                'facts': animal_data['facts'],
                'endangered_status': animal_data['endangered_status'],
                'fun_fact': animal_data['fun_fact'],
                'habitat': animal_data['habitat'],
                'diet': animal_data['diet'],
                'size': animal_data['size'],
                'threats': animal_data.get('threats', 'Unknown'),
                'population_trend': animal_data.get('population_trend', 'Unknown'),
                'image_filename': filename,
                'upload_id': str(upload.id),
                'model_type': 'ResNet50V2 Model'
            },
            'user': {
                'id': str(user.id),
                'username': user.username
            }
        })
        
    except Exception as e:
        print(f"Error in predict endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/predict_web', methods=['POST'])
@login_required
def predict_web():
    """Web form prediction endpoint - Returns HTML result page"""
    try:
        # Check if image file is present
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('dashboard'))
        
        image_file = request.files['file']
        
        # Check if file is selected
        if image_file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('dashboard'))
        
        # Check file extension
        if not allowed_file(image_file.filename):
            flash('Invalid file type. Please upload an image file (PNG, JPG, JPEG, GIF, BMP, WEBP).', 'error')
            return redirect(url_for('dashboard'))
        
        # Secure filename and save
        filename = secure_filename(image_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        img_path = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(img_path)
        
        # Get current user
        user = User.find_by_id(session['user_id'])
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Get geolocation if provided
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        latitude = float(lat) if lat else None
        longitude = float(lng) if lng else None
        
        # Identify animal using .h5 model (with Vision fallback)
        animal_data = identify_species_with_h5(img_path)

        if animal_data is None:
            # Quietly return user to dashboard without error messages
            return redirect(url_for('dashboard'))

        # Save prediction to database
        upload = Upload(
            filename=filename,
            species_name=animal_data['name'],
            confidence=animal_data['confidence'],
            user_id=ObjectId(session['user_id']),
            latitude=latitude,
            longitude=longitude
        )
        upload.save()
        
        # Update global statistics
        update_global_stats()
        
        # Return HTML result page
        return render_template(
            'result.html',
            species_name=animal_data['name'],
            scientific_name=animal_data.get('scientific_name', 'Unknown'),
            facts=animal_data['facts'],
            status=animal_data['endangered_status'],
            fun_fact=animal_data['fun_fact'],
            image_filename=filename,
            confidence=animal_data['confidence'],
            habitat=animal_data['habitat'],
            diet=animal_data['diet'],
            size=animal_data['size'],
            threats=animal_data.get('threats', 'Unknown'),
            population_trend=animal_data.get('population_trend', 'Unknown'),
            model_type='ResNet50V2 Model'
        )
        
    except Exception as e:
        print(f"Error in predict_web endpoint: {e}")
        flash(f'Error processing image: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/map")
def map_page():
    return render_template("map.html", maps_api_key=os.getenv('MAPS_API'))

# --- Friendly redirects for old/broken links (avoid 404) ---
@app.route("/ocean_game")
def ocean_game_redirect():
    flash('Feature coming soon. Explore the Map meanwhile!', 'info')
    return redirect(url_for('map_page'))

@app.route("/ocean_map")
def ocean_map_redirect():
    return redirect(url_for('map_page'))

@app.route("/settings")
def settings():
    if 'user_id' not in session:
        flash('Please login to access settings.', 'warning')
        return redirect(url_for('login'))
    
    user = User.find_by_id(session['user_id'])
    return render_template("settings.html", user=user)

@app.route("/marine_news")
def marine_news_redirect():
    return redirect(url_for('ocean_quiz'))

# Kids pages
@app.route("/species_explorer")
def species_explorer():
    return render_template('species_explorer.html')

@app.route("/ocean_quiz")
def ocean_quiz():
    return render_template('ocean_quiz.html')

@app.route("/ocean_stickers")
def ocean_stickers():
    return render_template('ocean_stickers.html')

@app.route("/ocean-explorer")
def ocean_explorer():
    return render_template('ocean_explorer.html')

@app.route("/save-ocean-game")
def save_ocean_game():
    return render_template('save_ocean_game.html')

@app.route("/export_data")
@login_required
def export_data():
    """Export user data"""
    try:
        user_id = session.get('user_id')
        uploads = list(Upload.find_by_user_id(user_id))
        
        # Create export data
        export_data = {
            "user": session.get('username'),
            "total_uploads": len(uploads),
            "identifications": [
                {
                    "species": upload.species_name,
                    "confidence": upload.confidence,
                    "date": upload.upload_date.strftime('%Y-%m-%d %H:%M')
                }
                for upload in uploads
            ]
        }
        
        return jsonify(export_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.find_by_id(session['user_id'])
    uploads = Upload.find_by_user_id(session['user_id'])[:10]  # Get latest 10
    
    # Get user statistics
    total_uploads = len(Upload.find_by_user_id(session['user_id']))
    user_uploads = Upload.find_by_user_id(session['user_id'])
    unique_species = len(set(upload.species_name for upload in user_uploads if upload.species_name))
    
    return render_template("dashboard.html", 
                           user=user, 
                           uploads=uploads, 
                           total_uploads=total_uploads, 
                           unique_species=unique_species)

@app.route("/profile")
@login_required
def profile():
    user = User.find_by_id(session['user_id'])
    uploads = Upload.find_by_user_id(session['user_id'])[:10]  # Get latest 10
    total_uploads = len(Upload.find_by_user_id(session['user_id']))
    unique_species = len(set(upload.species_name for upload in uploads if upload.species_name))
    return render_template("profile.html", user=user, uploads=uploads, total_uploads=total_uploads, unique_species=unique_species)

@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    try:
        user = User.find_by_id(session['user_id'])
        data = request.get_json()
        
        if data.get('username'):
            user.username = data['username']
        
        if data.get('email'):
            user.email = data['email']
        
        if data.get('bio') is not None:
            user.bio = data['bio']
        
        user.update(
            username=user.username,
            email=user.email,
            bio=user.bio
        )
        return jsonify({"success": True, "message": "Profile updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route("/api/stats")
def get_stats():
    """Get real-time global statistics"""
    try:
        stats = update_global_stats()
        if stats:
            return jsonify({
                "total_identifications": stats.total_identifications,
                "total_users": stats.total_users,
                "total_species": stats.total_species,
                "last_updated": stats.last_updated.isoformat()
            })
        else:
            return jsonify({
                "total_identifications": 0,
                "total_users": 0,
                "total_species": 0,
                "last_updated": datetime.utcnow().isoformat()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/species_locations')
def species_locations():
    """API endpoint to get locations for a specific species"""
    species = request.args.get('species')
    if not species:
        return jsonify({'error': 'Species parameter required'}), 400
    
    uploads = Upload.find_by_species(species)
    locations = [
        {
            'lat': u.latitude,
            'lng': u.longitude,
            'species': u.species_name,
            'timestamp': u.upload_date.isoformat() if u.upload_date else None
        }
        for u in uploads if u.latitude and u.longitude
    ]
    return jsonify(locations)

if __name__ == "__main__":
    app.run(debug=True)

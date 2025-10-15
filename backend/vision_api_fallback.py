#!/usr/bin/env python3
"""
Google Cloud Vision API fallback for AquaTrace AI
Used when H5 model fails to load or predict
"""

import os
import json
from google.cloud import vision
from PIL import Image
import io
import requests
from dotenv import load_dotenv

load_dotenv()

# Set up Google Cloud credentials
GOOGLE_CLOUD_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'cloud-api.json')

# Configure Gemini API
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        print("✅ Gemini API configured successfully!")
    else:
        gemini_model = None
        print("⚠️ Gemini API key not found")
except ImportError:
    gemini_model = None
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")
except Exception as e:
    gemini_model = None
    print(f"❌ Gemini setup error: {e}")

def setup_vision_client():
    """Initialize Google Cloud Vision client"""
    try:
        # Set the credentials environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CLOUD_CREDENTIALS
        
        # Initialize the client
        client = vision.ImageAnnotatorClient()
        print("✅ Google Cloud Vision API client initialized successfully!")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Vision API client: {e}")
        return None

def identify_marine_species_with_vision_api(image_path):
    """
    Identify marine species using Google Cloud Vision API
    Returns species information in the same format as H5 model
    """
    try:
        print("🔄 Using Google Cloud Vision API for species identification...")
        
        # Initialize Vision client
        client = setup_vision_client()
        if not client:
            raise Exception("Vision API client initialization failed")
        
        # Read the image file
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        # Create Vision API image object
        image = vision.Image(content=content)
        
        # Use object localization instead of label detection
        features = [{"type": vision.Feature.Type.OBJECT_LOCALIZATION}]
        
        # Also try text detection as backup
        text_features = [{"type": vision.Feature.Type.TEXT_DETECTION}]
        
        # Perform object localization
        response = client.annotate_image(request={"image": image, "features": features})
        objects = response.localized_object_annotations
        
        if response.error.message:
            raise Exception(f'Vision API error: {response.error.message}')
        
        print(f"📊 Vision API found {len(objects)} objects")
        
        # Marine species keywords to look for
        marine_keywords = {
            'fish': ['Fish', 'Tropical fish', 'Marine biology', 'Aquarium fish', 'Saltwater fish'],
            'sharks': ['Shark', 'Great white shark', 'Tiger shark', 'Hammerhead shark'],
            'turtle_tortoise': ['Sea turtle', 'Turtle', 'Marine turtle', 'Loggerhead turtle'],
            'dolphin': ['Dolphin', 'Marine mammal', 'Bottlenose dolphin'],
            'whale': ['Whale', 'Humpback whale', 'Blue whale', 'Marine mammal'],
            'octopus': ['Octopus', 'Cephalopod', 'Marine invertebrate'],
            'jelly fish': ['Jellyfish', 'Cnidaria', 'Marine invertebrate'],
            'seahorse': ['Seahorse', 'Marine fish'],
            'starfish': ['Starfish', 'Sea star', 'Echinoderm'],
            'crabs': ['Crab', 'Crustacean', 'Marine arthropod'],
            'lobster': ['Lobster', 'Crustacean'],
            'shrimp': ['Shrimp', 'Prawn', 'Crustacean'],
            'corals': ['Coral', 'Coral reef', 'Marine organism'],
            'sea urchins': ['Sea urchin', 'Echinoderm'],
            'eel': ['Eel', 'Moray eel', 'Electric eel'],
            'sea rays': ['Ray', 'Stingray', 'Manta ray', 'Skate'],
            'seal': ['Seal', 'Sea lion', 'Marine mammal'],
            'penguin': ['Penguin', 'Marine bird'],
            'puffers': ['Pufferfish', 'Blowfish']
        }
        
        # Find the best matching marine species
        best_match = None
        highest_confidence = 0
        
        for obj in objects:
            obj_name = obj.name
            confidence = obj.score
            
            print(f"🔍 Checking object: {obj_name} (confidence: {confidence:.2f})")
            
            # Check if this object matches any marine species
            for species, keywords in marine_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in obj_name.lower():
                        if confidence > highest_confidence:
                            highest_confidence = confidence
                            best_match = species
                            print(f"✅ Found marine species match: {species} ({confidence:.2f})")
                        break
        
        # If we found a marine species, return detailed info
        if best_match:
            species_name = best_match.replace('_', ' ').title()
            confidence_percentage = highest_confidence * 100
            
            print(f"🎯 Final identification: {species_name} ({confidence_percentage:.1f}%)")
            
            # Get detailed species information from Gemini API
            species_info = get_species_details_from_gemini(species_name)
            
            return {
                "name": species_name,
                "scientific_name": species_info["scientific_name"],
                "confidence": round(confidence_percentage, 1),
                "facts": species_info["facts"],
                "endangered_status": species_info["endangered_status"],
                "fun_fact": species_info["fun_fact"],
                "habitat": species_info["habitat"],
                "diet": species_info["diet"],
                "size": species_info["size"],
                "threats": species_info["threats"],
                "population_trend": species_info["population_trend"],
                "detection_method": "Google Cloud Vision API"
            }
        else:
            # No marine species found, return generic response
            print("⚠️ No marine species detected in image")
            return {
                "name": "Unknown Marine Species",
                "scientific_name": "Unknown",
                "confidence": 0,
                "facts": "Could not identify a specific marine species in this image using Google Cloud Vision API.",
                "endangered_status": "Unknown",
                "fun_fact": "Try uploading a clearer image of a marine animal.",
                "habitat": "Unknown",
                "diet": "Unknown",
                "size": "Unknown",
                "threats": "Unknown",
                "population_trend": "Unknown",
                "detection_method": "Google Cloud Vision API"
            }
            
    except Exception as e:
        print(f"❌ Vision API identification failed: {e}")
        return {
            "name": "Vision API Error",
            "scientific_name": "Unknown",
            "confidence": 0,
            "facts": f"Google Cloud Vision API error: {str(e)}",
            "endangered_status": "Unknown",
            "fun_fact": "Please try again or check your Vision API credentials.",
            "habitat": "Unknown",
            "diet": "Unknown",
            "size": "Unknown",
            "threats": "Unknown",
            "population_trend": "Unknown",
            "detection_method": "Google Cloud Vision API (Error)"
        }

def get_species_details_from_gemini(species_name):
    """Get detailed species information using Gemini API"""
    if not gemini_model:
        return {
            "scientific_name": "Unknown",
            "facts": f"This appears to be a {species_name}.",
            "endangered_status": "Unknown",
            "fun_fact": f"Interesting marine species: {species_name}",
            "habitat": "Marine environment",
            "diet": "Varies by species",
            "size": "Varies",
            "threats": "Climate change and human activities",
            "population_trend": "Unknown"
        }
    
    try:
        prompt = f"""
        Provide detailed information about the marine species: {species_name}
        
        Please provide the following information in JSON format:
        {{
            "scientific_name": "Scientific name of the species",
            "facts": "Brief description and key facts about this species",
            "endangered_status": "Conservation status (e.g., Least Concern, Vulnerable, Endangered)",
            "fun_fact": "An interesting fun fact about this species",
            "habitat": "Where this species typically lives",
            "diet": "What this species typically eats",
            "size": "Typical size range of this species",
            "threats": "Main threats to this species",
            "population_trend": "Current population trend (Stable, Increasing, Declining)"
        }}
        
        Make sure the response is valid JSON format only, no additional text.
        """
        
        print(f"🤖 Asking Gemini about {species_name}...")
        response = gemini_model.generate_content(prompt)
        
        # Parse JSON response
        species_info = json.loads(response.text)
        print(f"✅ Gemini provided details for {species_name}")
        
        return species_info
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return {
            "scientific_name": "Unknown",
            "facts": f"This appears to be a {species_name} identified by Vision API.",
            "endangered_status": "Unknown",
            "fun_fact": f"Marine species: {species_name}",
            "habitat": "Marine environment",
            "diet": "Varies by species", 
            "size": "Varies",
            "threats": "Climate change and human activities",
            "population_trend": "Unknown"
        }

def test_vision_api():
    """Test function to verify Vision API is working"""
    try:
        client = setup_vision_client()
        if client:
            print("🎉 Vision API is ready to use as fallback!")
            return True
        else:
            print("❌ Vision API setup failed")
            return False
    except Exception as e:
        print(f"❌ Vision API test failed: {e}")
        return False

if __name__ == "__main__":
    test_vision_api()

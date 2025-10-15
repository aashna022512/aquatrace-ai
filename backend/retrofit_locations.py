import random
from backend.models import Upload, uploads_collection
from backend.species_map_data import SPECIES_DISTRIBUTION

# Mapping from app species names to data keys
species_mapping = {
    "Dolphins": "dolphin",
    "Jellyfish": "jellyfish",
    "Sea Rays": "sea rays",
    "Starfish": "starfish",
    "Whales": "whale",
    "Sea Turtles": "sea_turtles",  # Placeholder, add if data available
    "Octopus": "octopus",  # Placeholder
    "Sharks": "sharks"  # Placeholder
}

def retrofit_locations():
    """Retrofit existing uploads with random locations based on species"""
    all_uploads = Upload.find()
    updated_count = 0
    skipped_count = 0
    
    print(f"Found {len(all_uploads)} existing uploads")
    
    for upload in all_uploads:
        if upload.latitude is not None and upload.longitude is not None:
            print(f"Skipping {upload.filename} - already has location")
            continue
        
        species_key = species_mapping.get(upload.species_name)
        if not species_key or species_key not in SPECIES_DISTRIBUTION:
            print(f"Skipping {upload.filename} ({upload.species_name}) - no location data")
            skipped_count += 1
            continue
        
        regions = SPECIES_DISTRIBUTION[species_key]["regions"]
        if not regions:
            skipped_count += 1
            continue
        
        # Pick random region
        region = random.choice(regions)
        lat = region["lat"]
        lng = region["lng"]
        
        # Update in database
        result = uploads_collection.update_one(
            {'_id': upload._id},
            {'$set': {'latitude': lat, 'longitude': lng}}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            print(f"Updated {upload.filename} ({upload.species_name}) with location: {lat}, {lng}")
        else:
            skipped_count += 1
    
    print(f"\nRetrofit complete!")
    print(f"Updated: {updated_count} uploads")
    print(f"Skipped: {skipped_count} uploads (already had location or no data)")

if __name__ == "__main__":
    retrofit_locations()

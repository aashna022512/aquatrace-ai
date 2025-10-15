"""
Species Distribution Data for Map Display
Contains geographical coordinates where marine species are commonly found
"""

SPECIES_DISTRIBUTION = {
    "dolphin": {
        "regions": [
            {"name": "Pacific Ocean", "lat": 0, "lng": -140, "population": "High"},
            {"name": "Atlantic Ocean", "lat": 30, "lng": -40, "population": "High"},
            {"name": "Mediterranean Sea", "lat": 40, "lng": 15, "population": "Medium"},
            {"name": "Indian Ocean", "lat": -10, "lng": 70, "population": "High"},
            {"name": "Caribbean Sea", "lat": 15, "lng": -75, "population": "Medium"}
        ],
        "description": "Dolphins are found in oceans worldwide, with highest populations in tropical waters."
    },
    "jellyfish": {
        "regions": [
            {"name": "Great Barrier Reef", "lat": -18, "lng": 147, "population": "High"},
            {"name": "Mediterranean Sea", "lat": 35, "lng": 18, "population": "High"},
            {"name": "North Sea", "lat": 56, "lng": 3, "population": "Medium"},
            {"name": "Japanese Waters", "lat": 35, "lng": 140, "population": "High"}
        ],
        "description": "Jellyfish are found in every ocean, from surface waters to the deep sea."
    },
    "sea rays": {
        "regions": [
            {"name": "Maldives", "lat": 3.2, "lng": 73.2, "population": "High"},
            {"name": "Great Barrier Reef", "lat": -16, "lng": 145, "population": "High"},
            {"name": "Red Sea", "lat": 22, "lng": 38, "population": "High"},
            {"name": "Caribbean Sea", "lat": 18, "lng": -78, "population": "Medium"}
        ],
        "description": "Sea rays prefer warm tropical waters, often found near coral reefs."
    },
    "starfish": {
        "regions": [
            {"name": "Pacific Northwest", "lat": 47, "lng": -123, "population": "High"},
            {"name": "Great Barrier Reef", "lat": -15, "lng": 145, "population": "High"},
            {"name": "Mediterranean Sea", "lat": 38, "lng": 15, "population": "Medium"},
            {"name": "Antarctic Waters", "lat": -70, "lng": 0, "population": "High"}
        ],
        "description": "Starfish are found in all oceans, from tropical reefs to cold polar waters."
    },
    "whale": {
        "regions": [
            {"name": "Alaska Waters", "lat": 60, "lng": -150, "population": "High"},
            {"name": "Antarctic Peninsula", "lat": -65, "lng": -60, "population": "High"},
            {"name": "Norway Coast", "lat": 69, "lng": 16, "population": "High"},
            {"name": "Baja California", "lat": 28, "lng": -114, "population": "High"}
        ],
        "description": "Whales migrate across all oceans, with feeding in polar waters."
    }
}

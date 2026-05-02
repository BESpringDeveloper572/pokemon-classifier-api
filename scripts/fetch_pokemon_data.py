import requests
import json
import os
import time

def fetch_all_pokemon_data(output_file="../app/data/pokemon_info.json"):
    """
    Fetches Name, Types, first English Pokédex description, Image URL, and Region for all 1,025 Pokémon.
    """
    base_url = "https://pokeapi.co/api/v2/pokemon/"
    species_url = "https://pokeapi.co/api/v2/pokemon-species/"
    
    # Mapping generation names to regions
    gen_to_region = {
        "generation-i": "Kanto",
        "generation-ii": "Johto",
        "generation-iii": "Hoenn",
        "generation-iv": "Sinnoh",
        "generation-v": "Unova",
        "generation-vi": "Kalos",
        "generation-vii": "Alola",
        "generation-viii": "Galar",
        "generation-ix": "Paldea"
    }
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    pokemon_db = {}
    total_pokemon = 1025
    
    print(f"Starting fetch for {total_pokemon} Pokémon...")
    
    for i in range(1, total_pokemon + 1):
        try:
            # 1. Fetch Basic Data (Types, Sprites)
            resp = requests.get(f"{base_url}{i}", timeout=10)
            data = resp.json()
            name = data["name"].capitalize()
            types = [t["type"]["name"].capitalize() for t in data["types"]]
            image_url = data["sprites"]["other"]["official-artwork"]["front_default"]
            
            # 2. Fetch Species Data (Description, Generation)
            species_resp = requests.get(f"{species_url}{i}", timeout=10)
            species_data = species_resp.json()
            
            # Find the first English entry in flavor_text_entries
            description = "No description available."
            for entry in species_data["flavor_text_entries"]:
                if entry["language"]["name"] == "en":
                    description = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                    break
            
            # Get Region from Generation
            gen_name = species_data["generation"]["name"]
            region = gen_to_region.get(gen_name, "Unknown")
            
            # 3. Store in Dictionary
            pokemon_db[name] = {
                "id": i,
                "types": types,
                "description": description,
                "image_url": image_url,
                "region": region
            }
            
            if i % 10 == 0:
                print(f"Progress: {i}/{total_pokemon} fetched...")
            
            # Small delay to be polite to the API
            time.sleep(0.1)
                
        except Exception as e:
            print(f"Error fetching ID {i}: {e}")
            continue

    # 4. Save to JSON
    with open(output_file, "w") as f:
        json.dump(pokemon_db, f, indent=4)
    
    print(f"\nSuccess! Data saved to {output_file}")

if __name__ == "__main__":
    fetch_all_pokemon_data()

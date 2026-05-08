import requests
import json
import os

def test_fetch(output_file="test_pokemon_info.json"):
    base_url = "https://pokeapi.co/api/v2/pokemon/"
    species_url = "https://pokeapi.co/api/v2/pokemon-species/"
    
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
    
    pokemon_db = {}
    total_pokemon = 5
    
    print(f"Starting test fetch for {total_pokemon} Pokémon...")
    
    for i in range(1, total_pokemon + 1):
        try:
            resp = requests.get(f"{base_url}{i}", timeout=10)
            data = resp.json()
            name = data["name"].capitalize()
            types = [t["type"]["name"].capitalize() for t in data["types"]]
            image_url = data["sprites"]["other"]["official-artwork"]["front_default"]
            
            species_resp = requests.get(f"{species_url}{i}", timeout=10)
            species_data = species_resp.json()
            
            description = "No description available."
            for entry in species_data["flavor_text_entries"]:
                if entry["language"]["name"] == "en":
                    description = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                    break
            
            gen_name = species_data["generation"]["name"]
            region = gen_to_region.get(gen_name, "Unknown")
            
            pokemon_db[name] = {
                "id": i,
                "types": types,
                "description": description,
                "image_url": image_url,
                "region": region
            }
            print(f"Fetched {name}")
                
        except Exception as e:
            print(f"Error fetching ID {i}: {e}")

    with open(output_file, "w") as f:
        json.dump(pokemon_db, f, indent=4)
    
    print(f"\nTest Success! Data saved to {output_file}")

if __name__ == "__main__":
    test_fetch()

import csv
import os
import random
from typing import List, Optional, Dict, Any

import pokebase as pb

class PokemonBase:
    """CSV-based data access with Pokebase enrichment."""
    GEN_TO_REGION = {
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

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._names: List[str] = []
        self._load_data()

    def _load_data(self):
        """Loads names from the CSV file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self._names = [row["name"] for row in reader if "name" in row]

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves Pokemon info by name, enriched via pokebase.
        """
        name_lower = name.lower()
        matched_name = next((n for n in self._names if n.lower() == name_lower), None)
        
        if not matched_name:
            return None

        try:
            p = pb.pokemon(name_lower)
            types = [t.type.name.capitalize() for t in p.types]
            species_data = p.species
            species_name = species_data.name.capitalize()
            
            s = pb.pokemon_species(name_lower)
            english_entries = [
                entry.flavor_text.replace("\n", " ").replace("\f", " ")
                for entry in s.flavor_text_entries
                if entry.language.name == "en"
            ]
            description = random.choice(english_entries) if english_entries else "No description available."
            
            gen_name = s.generation.name
            region = self.GEN_TO_REGION.get(gen_name, "Unknown")
            
            return {
                "id": p.id,
                "name": matched_name,
                "types": types,
                "description": description,
                "species": species_name,
                "height": p.height / 10.0,
                "weight": p.weight / 10.0,
                "region": region
            }
        except Exception:
            return {"name": matched_name}

    def get_all_names(self) -> List[str]:
        return self._names

import logging
import random
import os
import csv
from typing import Any

import pokebase as pb

logger = logging.getLogger(__name__)

class PokemonBase:
    """Dynamic data access using Pokebase."""
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

    def __init__(self):
        self._names : set[str] = set()
        self._phonetics : dict[str, str] = {}
        self._load_data()

    def _load_data(self):
        """Loads names and phonetics from local CSV."""
        csv_path = os.path.join(os.path.dirname(__file__), "data", "pokemon_tts_phonetics.csv")
        if not os.path.exists(csv_path):
            logger.error(f"Required phonetics CSV not found at {csv_path}")
            raise FileNotFoundError(f"Could not find {csv_path}")

        try:
            logger.info(f"Loading Pokémon data from {csv_path}...")
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['Name']
                    phonetic = row['Phonetic_TTS']
                    
                    self._names.add(name.capitalize())
                    self._phonetics[name.lower()] = phonetic
            logger.info(f"Successfully loaded {len(self._names)} Pokémon from CSV.")
        except Exception as e:
            logger.error(f"Error loading Pokémon CSV: {e}")
            raise RuntimeError("Could not initialize Pokémon data from CSV") from e

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Retrieves Pokemon info by name, enriched via pokebase.
        """
        name_lower = name.lower()
        # Verify it's a known pokemon name (case-insensitive check)
        matched_name = next((n for n in self._names if n.lower() == name_lower), None)
        
        if not matched_name:
            return None

        # Base info including phonetic if available
        result = {
            "name": matched_name,
            "pronunciation": self._phonetics.get(name_lower),
        }

        try:
            p = pb.pokemon(name_lower)
            types = [t.type.name.capitalize() for t in p.types]
            s = pb.pokemon_species(name_lower)
            species_name = next((g for g in s.genera if g.language.name == "en"), None).genus

            english_entries = [
                entry.flavor_text.replace("\n", " ").replace("\f", " ")
                for entry in s.flavor_text_entries
                if entry.language.name == "en"
            ]
            description = random.choice(english_entries) if english_entries else "No description available."
            
            gen_name = s.generation.name
            region = self.GEN_TO_REGION.get(gen_name, "Unknown")
            
            result.update({
                "id": p.id,
                "types": types,
                "description": description,
                "species": species_name,
                "height": p.height,
                "weight": p.weight,
                "region": region
            })
            return result
        except Exception as e:
            logger.error(f"Error enriching data for {name_lower}: {e}")
            return result

    def get_all_names(self) -> set[str]:
        return self._names

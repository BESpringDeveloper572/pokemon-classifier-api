import os
import random
import logging
from typing import List, Optional, Dict, Any

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
        self._names: List[str] = []
        self._load_data()

    def _load_data(self):
        """Loads names from PokéAPI."""
        try:
            logger.info("Fetching Pokémon names from PokéAPI...")
            # APIResourceList handles pagination and caching automatically
            self._names = [p['name'].capitalize() for p in pb.APIResourceList('pokemon')]
            logger.info(f"Successfully loaded {len(self._names)} names from PokéAPI.")
        except Exception as e:
            logger.error(f"Failed to fetch names from PokéAPI: {e}")
            raise RuntimeError("Could not initialize Pokémon name list") from e

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves Pokemon info by name, enriched via pokebase.
        """
        name_lower = name.lower()
        # Verify it's a known pokemon name (case-insensitive check)
        matched_name = next((n for n in self._names if n.lower() == name_lower), None)
        
        if not matched_name:
            return None

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
            
            return {
                "id": p.id,
                "name": matched_name,
                "types": types,
                "description": description,
                "species": species_name,
                "height": p.height,
                "weight": p.weight,
                "region": region
            }
        except Exception as e:
            logger.error(f"Error enriching data for {name_lower}: {e}")
            return {"name": matched_name}

    def get_all_names(self) -> List[str]:
        return self._names

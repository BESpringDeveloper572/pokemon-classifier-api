import json
import os
from typing import Protocol, Optional, Dict, Any, List

class PokemonInfo(Dict[str, Any]):
    """Type hint for Pokemon information dictionary."""
    id: int
    name: str
    types: List[str]
    description: str

class PokemonRepository(Protocol):
    """Interface for Pokemon metadata retrieval."""
    def get_by_name(self, name: str) -> Optional[PokemonInfo]:
        ...
    
    def get_all_names(self) -> List[str]:
        ...

class LocalJsonFilePokemonRepository:
    """JSON-based implementation of the PokemonRepository."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._metadata: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        """Loads data from the JSON file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self._metadata = json.load(f)

    def get_by_name(self, name: str) -> Optional[PokemonInfo]:
        """
        Retrieves Pokemon info by name (case-insensitive).
        """
        name_cap = name.capitalize()
        return self._metadata.get(name_cap)

    def get_all_names(self) -> List[str]:
        """Returns a list of all Pokemon names in the repository."""
        return list(self._metadata.keys())

# Helper function to get the default repository
def get_pokemon_repository() -> PokemonRepository:
    data_path = os.path.join(os.path.dirname(__file__), "data", "pokemon_info.json")
    return LocalJsonFilePokemonRepository(data_path)

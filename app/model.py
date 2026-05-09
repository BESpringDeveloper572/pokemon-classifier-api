import os
from transformers import pipeline
from PIL import Image
import torch

class PokemonClassifier:
    def __init__(self, model_name="skshmjn/Pokemon-classifier-gen9-1025"):
        self.hub_model_name = model_name
        model_slug = model_name.split("/")[-1]
        self.local_model_path = os.path.join(os.path.dirname(__file__), "data", "model", model_slug)
        
        # Determine best available device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        
        self.classifier = None

    def load_model(self):
        """Lazy load the model. Checks for local model first, then falls back to HF Hub."""
        if self.classifier is None:
            # Determine which path/name to use
            if os.path.exists(self.local_model_path) and os.path.isdir(self.local_model_path):
                model_to_load = self.local_model_path
                print(f"Loading model from local directory: {self.local_model_path}")
            else:
                model_to_load = self.hub_model_name
                print(f"Local model not found. Loading from Hugging Face Hub: {self.hub_model_name}")

            # Use device mapping for pipeline
            device_id = -1
            if self.device == "cuda":
                device_id = 0
            elif self.device == "mps":
                device_id = "mps"
            
            self.classifier = pipeline(
                "image-classification", 
                model=model_to_load,
                device=device_id
            )
        return self.classifier

    def predict(self, image: Image.Image, top_k=5):
        """Predict the Pokémon in the image."""
        classifier = self.load_model()
        results = classifier(image, top_k=top_k)
        return results

    @property
    def model_name(self):
        """Returns the active model path/name."""
        if os.path.exists(self.local_model_path):
            return f"Local ({self.local_model_path})"
        return f"Hub ({self.hub_model_name})"

# Singleton instance for the app
pokemon_classifier = PokemonClassifier()

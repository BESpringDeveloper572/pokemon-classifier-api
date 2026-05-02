from transformers import pipeline
from PIL import Image
import torch

class PokemonClassifier:
    def __init__(self, model_name="skshmjn/Pokemon-classifier-gen9-1025"):
        self.model_name = model_name
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        self.classifier = None

    def load_model(self):
        """Lazy load the model to save memory until needed."""
        if self.classifier is None:
            # Use device mapping for pipeline
            device_id = -1
            if self.device == "cuda":
                device_id = 0
            elif self.device == "mps":
                # Transformers pipeline uses the device string directly or index
                device_id = "mps"
            
            self.classifier = pipeline(
                "image-classification", 
                model=self.model_name,
                device=device_id
            )
        return self.classifier

    def predict(self, image: Image.Image, top_k=5):
        """Predict the Pokémon in the image."""
        classifier = self.load_model()
        results = classifier(image, top_k=top_k)
        return results

# Singleton instance for the app
pokemon_classifier = PokemonClassifier()

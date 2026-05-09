from transformers import AutoModelForImageClassification, AutoImageProcessor
import os

def download_model(model_name="skshmjn/Pokemon-classifier-gen9-1025", save_directory="app/data/model"):
    """
    Downloads the model and processor from Hugging Face and saves them locally.
    """
    print(f"Downloading model '{model_name}'...")
    
    # Ensure the directory exists
    os.makedirs(save_directory, exist_ok=True)
    
    try:
        # Download and save
        model = AutoModelForImageClassification.from_pretrained(model_name)
        processor = AutoImageProcessor.from_pretrained(model_name)
        
        model.save_pretrained(save_directory)
        processor.save_pretrained(save_directory)
        
        print(f"Success! Model and processor saved to '{save_directory}'")
    except Exception as e:
        print(f"Error downloading model: {e}")

if __name__ == "__main__":
    download_model()

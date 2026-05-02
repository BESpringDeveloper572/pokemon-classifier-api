import io
import json
import os
from typing import Annotated

from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends

from .model import pokemon_classifier

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Pokémon Classifier API",
    description="A REST API to classify Pokémon from images using a Vision Transformer (ViT) model.",
    version="1.0.0"
)

# --- SECURITY (FROM ENVIRONMENT) ---
API_KEY = os.getenv("POKEMON_API_KEY", "CHANGEME_PLEASE")

def verify_api_key(
    x_api_key: str = Header(None)
):
    """Security dependency to check for the API Key."""
    # Check API Key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing X-API-KEY header.")
    
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key.")
    
    return x_api_key

# --- METADATA LOADING ---
METADATA_PATH = os.path.join(os.path.dirname(__file__), "data", "pokemon_info.json")
pokemon_metadata = {}

if os.path.exists(METADATA_PATH):
    with open(METADATA_PATH, "r") as f:
        pokemon_metadata = json.load(f)

@app.get("/")
async def root(api_key: Annotated[str, Depends(verify_api_key)]):
    return {
        "message": "Welcome to the Pokémon Classifier API!",
        "docs": "/docs",
        "model": pokemon_classifier.model_name,
        "metadata_loaded": len(pokemon_metadata) > 0
    }

@app.get("/pokemon/{name}")
async def get_pokemon_by_name(name: str):
    """
    Get Pokémon details by name.
    """
    name_cap = name.capitalize()
    info = pokemon_metadata.get(name_cap)
    
    if info:
        return {
            "pokemon": name_cap,
            "id": info.get("id"),
            "types": info.get("types"),
            "description": info.get("description")
        }
    else:
        return {
            "pokemon": name_cap,
            "info": "Metadata not found. Run the fetch script to populate data."
        }

@app.post(
    "/classify",
    responses={
        400: {"description": "File must be an image."},
        500: {"description": "Error processing image"}
    },
)
# file: UploadFile = File(...)
async def classify_image(
    file: Annotated[UploadFile, Depends(File(...))]
):
    """
    Classify a Pokémon from an uploaded image and return its details.
    """
    # Verify file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        # Read file content
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
        
        # Perform prediction
        predictions = pokemon_classifier.predict(image, top_k=1)
        if not predictions:
            return {"pokemon": "Unknown", "info": None}
            
        raw_name = predictions[0]["label"]
        name_cap = raw_name.capitalize()
        info = pokemon_metadata.get(name_cap)
        
        if info:
            return {
                "pokemon": name_cap,
                "id": info.get("id"),
                "types": info.get("types"),
                "description": info.get("description")
            }
        else:
            return {
                "pokemon": name_cap,
                "info": "Metadata not found. Run the fetch script to populate data."
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

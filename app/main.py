import io
import os
from typing import Annotated

from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.security import APIKeyHeader

from .model import pokemon_classifier
from .repository import get_pokemon_repository, PokemonRepository

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION & SECURITY ---
API_KEY = os.getenv("POKEMON_API_KEY", "CHANGEME_PLEASE")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mpo", ".bmp"}

# Initialize Repository
pokemon_repo: PokemonRepository = get_pokemon_repository()

def verify_api_key(
    x_api_key: str = Depends(api_key_header)
):
    """Security dependency to check for the API Key."""
    # Check API Key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing X-API-KEY header.")
    
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key.")
    
    return x_api_key

def validate_image_header(content: bytes) -> bool:
    """
    Check if the file content starts with common image magic numbers.
    """
    # JPEG (including MPO)
    if content.startswith(b"\xff\xd8\xff"):
        return True
    # PNG
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # WEBP
    if content.startswith(b"RIFF") and b"WEBP" in content[8:12]:
        return True
    # GIF
    if content.startswith(b"GIF8"):
        return True
    # BMP
    if content.startswith(b"BM"):
        return True
    return False

app = FastAPI(
    title="Pokémon Classifier API",
    description="A REST API to classify Pokémon from images using a Vision Transformer (ViT) model.",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)]
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Pokémon Classifier API!",
        "docs": "/docs",
        "model": pokemon_classifier.model_name,
        "metadata_loaded": len(pokemon_repo.get_all_names()) > 0
    }

@app.get("/pokemon/{name}")
async def get_pokemon_by_name(name: str):
    """
    Get Pokémon details by name.
    """
    info = pokemon_repo.get_by_name(name)
    
    if info:
        return {
            "pokemon": info.get("name") or name.capitalize(),
            "id": info.get("id"),
            "types": info.get("types"),
            "description": info.get("description")
        }
    else:
        return {
            "pokemon": name.capitalize(),
            "info": "Metadata not found. Run the fetch script to populate data."
        }

@app.post(
    "/classify",
    responses={
        400: {"description": "File must be an image or exceeds size limit."},
        500: {"description": "Error processing image"}
    },
)
async def classify_image(
    file: Annotated[UploadFile, File(...)],
    user_agent: Annotated[str | None, Header()] = None
):
    """
    Classify a Pokémon from an uploaded image and return its details.
    Includes security validation for file type and size.
    """
    # 1. Basic Content-Type check (can be spoofed)
    is_3ds = user_agent and "3DS" in user_agent.upper()
    if not file.content_type.startswith("image/") and not is_3ds:
        raise HTTPException(status_code=400, detail="File must be an image.")

    # 2. Size validation (prevent DoS)
    file_size = getattr(file, "size", None)
    if file_size and file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE/(1024*1024)}MB.")

    try:
        # Read file content
        content = await file.read()
        
        # 3. Double check size if file.size was missing
        if len(content) > MAX_FILE_SIZE:
             raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE/(1024*1024)}MB.")

        # 4. Magic number validation (Content-type bypass protection)
        if not validate_image_header(content):
            raise HTTPException(status_code=400, detail="Invalid image format (magic number mismatch).")

        # 5. PIL validation
        image = Image.open(io.BytesIO(content))
        
        # If it's a 3DS or a multi-frame image (like MPO), ensure we get the first frame
        if getattr(image, "n_frames", 1) > 1:
            image.seek(0)
            
        # Convert to RGB (required for the ViT model)
        image = image.convert("RGB")
        
        # Perform prediction
        predictions = pokemon_classifier.predict(image, top_k=1)
        if not predictions:
            return {"pokemon": "Unknown", "info": None}
            
        raw_name = predictions[0]["label"]
        info = pokemon_repo.get_by_name(raw_name)
        
        if info:
            return {
                "pokemon": info.get("name") or raw_name.capitalize(),
                "id": info.get("id"),
                "types": info.get("types"),
                "description": info.get("description")
            }
        else:
            return {
                "pokemon": raw_name.capitalize(),
                "info": "Metadata not found. Run the fetch script to populate data."
            }
            
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

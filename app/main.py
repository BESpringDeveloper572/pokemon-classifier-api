import io
import logging
import os
from typing import Annotated

import requests
from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from rembg import remove

from .model import PokemonClassifier
from .pokemon_api import PokemonBase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- SCHEMA ---
class PokemonSchema(BaseModel):
    name: str
    id: int | None = None
    types: list[str] | None = None
    description: str | None = None
    species: str | None = None
    height: float | None = None
    weight: float | None = None
    region: str | None = None

# --- CONFIGURATION & SECURITY ---
API_KEY = os.getenv("POKEMON_API_KEY", "CHANGEME_PLEASE")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

COMMON_RESPONSES = {
    401: {"description": "Unauthorized: Missing X-API-KEY header."},
    403: {"description": "Forbidden: Invalid API Key."},
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit

# Initialize Data Access
pokemon_repo = PokemonBase()

# Initialize Classifier
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "skshmjn/Pokemon-classifier-gen9-1025")
pokemon_classifier = PokemonClassifier(model_name=DEFAULT_MODEL_NAME)

def verify_api_key(
    x_api_key: str = Depends(api_key_header)
):
    """Security dependency to check for the API Key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing X-API-KEY header.")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key.")
    return x_api_key

def validate_image_header(content: bytes) -> bool:
    if content.startswith(b"\xff\xd8"): return True
    if content.startswith(b"\x89PNG\r\n\x1a\n"): return True
    if content.startswith(b"RIFF") and b"WEBP" in content[8:12]: return True
    if content.startswith(b"GIF8"): return True
    if content.startswith(b"BM"): return True
    return False

app = FastAPI(
    title="Pokémon Classifier API",
    description="A REST API to classify Pokémon from images and return 3DS-ready sprites.",
    version="1.1.0",
    dependencies=[Depends(verify_api_key)]
)

# --- ROUTES ---

@app.get("/", responses=COMMON_RESPONSES)
async def root():
    return {
        "message": "Welcome to the Pokémon Classifier API!",
        "docs": "/docs",
        "model": pokemon_classifier.model_name,
        "metadata_loaded": len(pokemon_repo.get_all_names()) > 0
    }

@app.get("/pokemon/{name}", response_model=PokemonSchema, responses={**COMMON_RESPONSES, 404: {"description": "Pokemon not found"}})
async def get_pokemon_by_name(name: str):
    info = pokemon_repo.get_by_name(name)
    if info:
        return info
    raise HTTPException(status_code=404, detail="Pokemon not found")

@app.get("/pokemon/{name}/sprite", responses={**COMMON_RESPONSES, 404: {"description": "Sprite not found"}, 500: {"description": "Error processing sprite"}})
async def get_pokemon_sprite(name: str, size: int = 64):
    info = pokemon_repo.get_by_name(name)
    if not info or not info.get("id"):
        raise HTTPException(status_code=404, detail="Sprite not found")

    try:
        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{info['id']}.png"
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        
        if size % 8 != 0:
            size = (size // 8 + 1) * 8
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        from .utils import tile_image_for_3ds
        tiled_bytes = tile_image_for_3ds(img)
        
        return Response(
            content=tiled_bytes,
            media_type="application/octet-stream",
            headers={
                "X-Sprite-Width": str(size),
                "X-Sprite-Height": str(size)
            }
        )
    except Exception as e:
        logger.error(f"Error processing sprite: {e}")
        raise HTTPException(status_code=500, detail="Error processing sprite")

@app.post("/classify", response_model=PokemonSchema, responses={**COMMON_RESPONSES, 400: {"description": "Invalid input (size or format)"}, 404: {"description": "Could not classify image"}, 500: {"description": "Internal server error during classification"}})
async def classify_image(
    file: Annotated[UploadFile, File(...)],
    user_agent: Annotated[str | None, Header()] = None
):
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
             raise HTTPException(status_code=400, detail="File too large.")

        is_3ds = user_agent and "3DS" in user_agent.upper()

        if is_3ds:
            size = len(content)
            if size == 192000:
                rgb_data = bytearray(400 * 240 * 3)
                for x in range(240):
                    for y in range(400):
                        offset = (x * 400 + y) * 2
                        word = content[offset] | (content[offset + 1] << 8)
                        rgb_data[(y * 240 + x) * 3] = ((word >> 11) & 0x1F) << 3
                        rgb_data[(y * 240 + x) * 3 + 1] = ((word >> 5) & 0x3F) << 2
                        rgb_data[(y * 240 + x) * 3 + 2] = (word & 0x1F) << 3
                image = Image.frombytes("RGB", (240, 400), bytes(rgb_data)).rotate(90, expand=True)
        else:
            if not validate_image_header(content):
                raise HTTPException(status_code=400, detail="Invalid image type")
            else:
                try:
                    image = Image.open(io.BytesIO(content))
                except (UnidentifiedImageError, ValueError):
                    raise HTTPException(status_code=400, detail="Invalid image content")

        try:
            image = remove(image)
            if image.mode == 'RGBA':
                white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
                image = Image.alpha_composite(white_bg, image).convert("RGB")
            else:
                image = image.convert("RGB")
        except Exception as rb_err:
            logger.error(f"Rembg error: {rb_err}")
            image = image.convert("RGB")

        predictions = pokemon_classifier.predict(image, top_k=1)
        if not predictions:
            raise HTTPException(status_code=404, detail="Could not classify image")
            
        raw_name = predictions[0]["label"]
        info = pokemon_repo.get_by_name(raw_name)
        
        if not info:
             return {"name": raw_name.capitalize()}
             
        return info
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Classification error")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

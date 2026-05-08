import io
import json
import os
import logging
from typing import Annotated

from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from .model import pokemon_classifier
from .repository import get_pokemon_repository, PokemonRepository

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION & SECURITY ---
API_KEY = os.getenv("POKEMON_API_KEY", "CHANGEME_PLEASE")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit
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

app = FastAPI(
    title="Pokémon Classifier API",
    description="A REST API to classify Pokémon from images using a Vision Transformer (ViT) model.",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)]
)

# --- EXCEPTION HANDLERS ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Log HTTP exceptions (like 400 Bad Request) without logging the request body."""
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors without logging the request body."""
    logger.error(
        f"Validation error on {request.method} {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Log unhandled server-side exceptions."""
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# --- ROUTES ---

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
    Includes security validation for file size and image integrity.
    """
    # 1. Size validation (prevent DoS) - check header first if available
    file_size = getattr(file, "size", None)
    if file_size and file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE/(1024*1024)}MB.")

    try:
        # Read file content
        content = await file.read()
        
        # 2. Check size again based on actual bytes read
        if len(content) > MAX_FILE_SIZE:
             raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE/(1024*1024)}MB.")

        # 3. PIL validation and processing
        try:
            try:
                image = Image.open(io.BytesIO(content))
                
                # If it's a multi-frame image (like 3DS MPO or GIF), ensure we get the first frame
                if getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1:
                    image.seek(0)
                    
                # Convert to RGB (required for the ViT model)
                image = image.convert("RGB")
            except (UnidentifiedImageError, ValueError):
                # Fallback for 3DS Raw Screen Dumps (Top Screen)
                # Detection based on common file sizes
                size = len(content)
                if size == 288000:  # 240x400 BGR888
                    logger.info("Detected 3DS Raw Buffer: 240x400 BGR888")
                    image = Image.frombytes("RGB", (240, 400), content, "raw", "BGR")
                    image = image.rotate(90, expand=True)
                elif size == 192000:  # 240x400 RGB565 (Column-Major)
                    # Log the first 16 bytes to help debug byte order
                    first_bytes_hex = content[:16].hex(" ")
                    logger.info(f"Detected 3DS Raw Buffer (192,000 bytes). First 16: {first_bytes_hex}")
                    
                    try:
                        logger.info("Decoding Column-Major RGB565 buffer...")
                        # 3DS buffers are often stored in columns: 240 columns, each 400 pixels high.
                        # Each pixel is 2 bytes (RGB565 Little Endian).
                        rgb_data = bytearray(400 * 240 * 3)
                        
                        # Unpack column-major to row-major RGB
                        for x in range(240):
                            for y in range(400):
                                # Offset in raw buffer (column-major)
                                offset = (x * 400 + y) * 2
                                # Little Endian RGB565
                                b1 = content[offset]
                                b2 = content[offset + 1]
                                word = b1 | (b2 << 8)
                                
                                # Extract RGB565 components
                                # RRRRR GGGGGG BBBBB
                                r = ((word >> 11) & 0x1F) << 3
                                g = ((word >> 5) & 0x3F) << 2
                                b = (word & 0x1F) << 3
                                
                                # Target position (row-major: y is row, x is col)
                                # We want a 400x240 image
                                target_idx = (y * 240 + x) * 3
                                rgb_data[target_idx] = r
                                rgb_data[target_idx+1] = g
                                rgb_data[target_idx+2] = b
                        
                        # Create image (400x240 is the standard top screen aspect ratio)
                        image = Image.frombytes("RGB", (240, 400), bytes(rgb_data))
                        # The screen is physically 400x240, so our (240x400) needs rotation
                        # or we just interpreted x/y as 240x400. 
                        # Based on 3DS specs, it's 400x240.
                        image = Image.frombytes("RGB", (240, 400), bytes(rgb_data))
                        image = image.rotate(90, expand=True)
                    except Exception as e:
                        logger.error(f"RGB565 decoding failed: {e}")
                        raise HTTPException(status_code=400, detail="Failed to decode 3DS raw buffer.")
                else:
                    logger.warning(f"Validation failed for unsupported file size: {size} bytes")
                    raise HTTPException(status_code=400, detail="Uploaded file is not a valid or supported image.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error decoding raw image: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to decode raw image buffer.")
        
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
        # Re-raise HTTPException to be handled by our custom handler
        raise
    except Exception as e:
        # Unhandled exceptions will be caught by our general_exception_handler
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

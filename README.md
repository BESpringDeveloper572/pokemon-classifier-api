# Pokémon Classifier REST API

A REST API built with FastAPI that uses a Vision Transformer (ViT) model (`skshmjn/Pokemon-classifier-gen9-1025`) to classify Pokémon from uploaded images and retrieve enriched metadata via PokéAPI.

## Features
- **FastAPI**: High-performance, modern web framework.
- **Vision Transformer**: Fine-tuned ViT for high-accuracy Pokémon classification.
- **Full Gen 9 Support**: Recognizes all 1,025 Pokémon.
- **Dynamic Metadata**: Enriches results with real-time data from PokéAPI (types, description, region, etc.).
- **3DS Compatibility**: 
    - Supports raw 3DS framebuffer uploads (BGR565).
    - Provides a `/sprite` endpoint that returns 3DS-native 8x8 tiled RGBA8888 sprites.
- **Background Removal**: Uses `rembg` to improve classification accuracy by focusing on the subject.

## Installation

1.  **Clone or navigate to the project**:
    ```bash
    cd pokemon-classifier-api
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    POKEMON_API_KEY=your_secret_api_key
    MODEL_NAME=skshmjn/Pokemon-classifier-gen9-1025
    ```

## Running the API

Start the server using `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Health Check**: `GET http://localhost:8000/` (Requires `X-API-KEY`)
- **Swagger Documentation**: `http://localhost:8000/docs`

## Authentication

The API uses header-based authentication for all endpoints.

- **Header**: `X-API-KEY`
- **Value**: The key defined in your `.env` file (defaults to `CHANGEME_PLEASE` if not set).

## Usage

### Classify an Image
`POST /classify`

Standard multipart/form-data upload:
```bash
curl -X POST "http://localhost:8000/classify" \
     -H "X-API-KEY: your_secret_api_key" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/pokemon_image.png"
```

**Nintendo 3DS Support**:
If the `User-Agent` contains "3DS", the API accepts a raw 400x240 BGR565 framebuffer (192,000 bytes) and automatically rotates it 90 degrees for processing.

### Get Pokémon Details by Name
`GET /pokemon/{name}`

```bash
curl -X GET "http://localhost:8000/pokemon/pikachu" \
     -H "X-API-KEY: your_secret_api_key"
```

### Get 3DS-Native Sprite
`GET /pokemon/{name}/sprite`

Returns an 8x8 tiled RGBA8888 byte stream, ready for the 3DS GPU (PICA200).
```bash
curl -X GET "http://localhost:8000/pokemon/pikachu/sprite?size=64" \
     -H "X-API-KEY: your_secret_api_key" \
     --output pikachu.bin
```

## Utility Scripts

- **Pre-download Model**: Cache the Hugging Face model locally before starting the server.
  ```bash
  python scripts/download_model.py
  ```

## Metadata Enrichment
Metadata is fetched dynamically via the `pokebase` library, which interacts with the [PokéAPI](https://pokeapi.co/). Names are loaded at startup, and full details are retrieved and cached on demand.

## Model Details
The API uses a fine-tuned Vision Transformer (ViT) model. Upon upload, images undergo background removal via `rembg` and normalization before being passed to the classifier.

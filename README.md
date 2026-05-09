# Pokémon Classifier REST API

A REST API that uses a Vision Transformer (ViT) model (`skshmjn/Pokemon-classifier-gen9-1025`) to classify Pokémon from uploaded images and retrieve metadata.

## Features
- **FastAPI**: Modern, fast web framework.
- **Vision Transformer**: High-accuracy classification.
- **Gen 9 Support**: Classifies up to 1,025 different Pokémon.
- **Metadata Lookup**: Retrieve Pokémon details by name or image.

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
    ```

## Running the API

Start the server using `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Health Check**: `GET http://localhost:8000/` (Requires `X-API-KEY`)
- **Swagger Documentation**: `http://localhost:8000/docs`

## Authentication

The API uses header-based authentication for specific endpoints (like the health check).

- **Header**: `X-API-KEY`
- **Value**: The key defined in your `.env` file (defaults to `CHANGEME_PLEASE` if not set).

## Fetching Pokémon Metadata

To fetch names, types, and descriptions for all 1,025 Pokémon from PokéAPI, run the provided script. This data is used to enrich the classifier results.

### Using Terminal
```bash
python scripts/fetch_pokemon_data.py
```

### Using PyCharm
1. Right-click the `scripts/fetch_pokemon_data.py` file in the project tree.
2. Select **Run 'fetch_pokemon_data'**.
3. The data will be saved to `app/data/pokemon_info.json`.

## Usage

### Classify an Image
`POST /classify`

```bash
curl -X POST "http://localhost:8000/classify" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/pokemon_image.png"
```

### Get Pokémon Details by Name
`GET /pokemon/{name}`

```bash
curl -X GET "http://localhost:8000/pokemon/pikachu"
```

### Health Check (Authenticated)
`GET /`

```bash
curl -H "X-API-KEY: your_secret_api_key" http://localhost:8000/
```

## Model Details
The API uses the `skshmjn/Pokemon-classifier-gen9-1025` model from Hugging Face, which is a fine-tuned Vision Transformer (ViT). It returns the top Pokémon prediction enriched with metadata from the local cache.

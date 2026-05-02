# Pokémon Classifier REST API

A REST API that uses a Vision Transformer (ViT) model (`skshmjn/Pokemon-classifier-gen9-1025`) to classify Pokémon from uploaded images.

## Features
- **FastAPI**: Modern, fast web framework.
- **Vision Transformer**: High-accuracy classification.
- **Gen 9 Support**: Classifies up to 1,025 different Pokémon.

## Installation

1.  **Clone or navigate to the project**:
    ```bash
    cd pokemon-classifier-api
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the API

Start the server using `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Health Check**: `GET http://localhost:8000/`
- **Swagger Documentation**: `http://localhost:8000/docs`

## Running in PyCharm

1. **Open Project**: Open the `pokemon-classifier-api` folder in PyCharm.
2. **Configure Interpreter**:
   - Go to `Settings` > `Project: pokemon-classifier-api` > `Python Interpreter`.
   - Click `Add Interpreter` > `Add Local Interpreter...`.
   - Select `System Interpreter` and ensure it points to the Python version where you installed the requirements (usually `/usr/bin/python3` or similar).
   - If you see a warning about `uvicorn` not found, make sure the interpreter path matches the one where `pip install` was run.
3. **Create Run Configuration**:
   - Click `Add Configuration...` in the top right.
   - Click `+` and select `FastAPI`.
   - **Application**: Select `app/main.py`.
   - **Uvicorn Options**: Add `--host 0.0.0.0 --port 8000 --reload`.
   - Click `OK` and then the green "Run" arrow.

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

### Using `curl`

```bash
curl -X POST "http://localhost:8000/classify" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/pokemon_image.png"
```

### Using the Swagger UI
1. Navigate to `http://localhost:8000/docs`.
2. Find the `/classify` endpoint.
3. Click "Try it out", upload an image, and click "Execute".

## Model Details
The API uses the `skshmjn/Pokemon-classifier-gen9-1025` model from Hugging Face, which is a fine-tuned Vision Transformer (ViT). It returns the top 5 most likely Pokémon for each uploaded image.

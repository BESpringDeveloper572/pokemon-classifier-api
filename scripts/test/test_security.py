import io
import os

from PIL import Image
from fastapi.testclient import TestClient

# Set a dummy API key for testing BEFORE importing app
os.environ["POKEMON_API_KEY"] = "testkey"

from app.main import app

client = TestClient(app)

def test_valid_image():
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    headers = {"X-API-KEY": "testkey"}
    files = {"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    response = client.post("/classify", headers=headers, files=files)
    assert response.status_code == 200
    print("Valid image test passed!")

def test_invalid_magic_number():
    # Content-Type is image/jpeg but content is text
    content = b"This is definitely not an image."
    headers = {"X-API-KEY": "testkey"}
    files = {"file": ("test.jpg", content, "image/jpeg")}
    response = client.post("/classify", headers=headers, files=files)
    assert response.status_code == 400
    assert "Invalid image format" in response.json()["detail"]
    print("Invalid magic number test passed!")

def test_large_file():
    # Create a 6MB dummy content (limit is 5MB)
    content = b"0" * (6 * 1024 * 1024)
    headers = {"X-API-KEY": "testkey"}
    files = {"file": ("test.jpg", content, "image/jpeg")}
    response = client.post("/classify", headers=headers, files=files)
    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]
    print("Large file test passed!")

if __name__ == "__main__":
    test_valid_image()
    test_invalid_magic_number()
    test_large_file()
    print("All security validation tests passed!")

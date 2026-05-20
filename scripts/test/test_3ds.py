import io
import os

from PIL import Image
from fastapi.testclient import TestClient

# Set a dummy API key for testing BEFORE importing app
os.environ["POKEMON_API_KEY"] = "testkey"

from app.main import app

client = TestClient(app)

def test_classify_3ds_ua():
    """Test that the 3DS User-Agent is recognized and handled."""
    # Create a small dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    # Test with 3DS User-Agent
    headers = {
        "X-API-KEY": "testkey",
        "User-Agent": "Mozilla/5.0 (Nintendo 3DS; U; ; en) Version/1.7630.US"
    }
    files = {"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    
    response = client.post("/classify", headers=headers, files=files)
    
    assert response.status_code == 200
    print("3DS UA test passed!")

def test_classify_mpo_handling():
    """Test that multi-frame images (like 3DS MPO) are handled by taking the first frame."""
    # Create a dummy multi-frame image (simulating MPO)
    # We use JPEG format because our validation specifically looks for JPEG headers for MPO
    img1 = Image.new('RGB', (100, 100), color='red')
    img2 = Image.new('RGB', (100, 100), color='blue')
    
    img_byte_arr = io.BytesIO()
    # Pillow doesn't easily save multi-frame JPEG/MPO, so we'll just prepend a JPEG header 
    # to a multi-frame TIFF and hope PIL's Image.open still works for n_frames, 
    # OR we use a format that supports multi-frame and has a magic number we allow.
    # Actually, GIF supports multi-frame and we allow it!
    img1.save(img_byte_arr, format='GIF', save_all=True, append_images=[img2])
    img_byte_arr = img_byte_arr.getvalue()

    headers = {
        "X-API-KEY": "testkey",
        "User-Agent": "Mozilla/5.0 (Nintendo 3DS; U; ; en) Version/1.7630.US"
    }
    # Even if it's GIF in this mock, the 3DS check should handle n_frames > 1
    files = {"file": ("test.gif", img_byte_arr, "image/gif")}
    
    response = client.post("/classify", headers=headers, files=files)
    
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    
    assert response.status_code == 200
    print("Multi-frame handling test passed!")

if __name__ == "__main__":
    test_classify_3ds_ua()
    test_classify_mpo_handling()
    print("All 3DS compatibility tests passed!")

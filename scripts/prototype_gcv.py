
import os
import io
from google.cloud import vision

def reverse_image_search_gcv(image_path):
    """
    Uses Google Cloud Vision API's Web Detection to find top matching web results.
    Note: Requires GOOGLE_APPLICATION_CREDENTIALS environment variable to be set.
    """
    # Initialize the client
    client = vision.ImageAnnotatorClient()

    # Load the image into memory
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Perform web detection
    response = client.web_detection(image=image)
    annotations = response.web_detection

    results = []

    if annotations.pages_with_matching_images:
        print(f"\n{len(annotations.pages_with_matching_images)} Pages with matching images found:")
        for page in annotations.pages_with_matching_images[:5]:
            print(f"URL: {page.url}")
            print(f"Title: {page.page_title}")
            results.append({
                "url": page.url,
                "title": page.page_title
            })
            
    if annotations.web_entities:
        print(f"\n{len(annotations.web_entities)} Web entities found:")
        for entity in annotations.web_entities[:5]:
            print(f"Entity: {entity.description} (Score: {entity.score})")

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
                
    return results

if __name__ == "__main__":
    # This is a standalone prototype.
    # To test this, you'll need to set:
    # export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
    
    test_image = "test_pokemon.jpg" # Replace with a real path for testing
    if os.path.exists(test_image):
        try:
            reverse_image_search_gcv(test_image)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Please provide a test image at {test_image} to run this prototype.")

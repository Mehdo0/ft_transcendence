import base64
import requests
import json

# 1. Configuration
API_URL = "http://127.0.0.1:8000/api/ai_guess/"
IMAGE_PATH = "apple.png" # Path to your test image

def test_my_ai():
    # 2. Open the image and convert it to Base64
    with open(IMAGE_PATH, "rb") as image_file:
        raw_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
    # 3. Add the HTML Canvas prefix that your backend is looking for
    full_base64_string = f"data:image/png;base64,{raw_base64}"
    print (full_base64_string)
    # 4. Build the JSON payload EXACTLY matching your Pydantic Drawing model
    payload = {
        "user_id": 1,
        "Base64_drawing": full_base64_string,
        "timer": 45,                  # Simulating 45 seconds elapsed
        "current_word": "apple",      # The word they were supposed to draw
        "ai_results": {}              # Empty dict for initialization
    }
    
    # 5. Send the POST request to your Docker server
    print(f"Sending drawing to {API_URL}...")
    response = requests.post(API_URL, json=payload)
    
    # 6. Print the results
    print(f"Status Code: {response.status_code}")
    try:
        # Print the beautiful JSON response your server sends back
        print(json.dumps(response.json(), indent=4))
    except Exception:
        # If it crashes (e.g. 500 Internal Server Error), print the raw text
        print(response.text)

if __name__ == "__main__":
    test_my_ai()
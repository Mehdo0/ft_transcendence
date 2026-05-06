import base64
import requests
import json

# ==========================================
# 1. CONFIGURATION
# ==========================================
BASE_URL = "http://127.0.0.1:8000"
IMAGE_PATH = "apple.png" # Ensure this file exists on your computer

# IMPORTANT: You must use an account that actually exists in your SQLite DB!
# If you haven't created one with a password yet, you need to register one.
TEST_USERNAME = "PlayerOne"
TEST_PASSWORD = "mysecretpassword" 

def test_ai_microservice():
    # ==========================================
    # STEP 1: LOG IN TO GET THE TOKEN
    # ==========================================
    print(f"--- 1. Logging in as '{TEST_USERNAME}' ---")
    
    # Notice we are sending form data (data=) not JSON, because of OAuth2 rules!
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    token_response = requests.post(f"{BASE_URL}/token", data=login_data)
    
    if token_response.status_code != 200:
        print("❌ Login Failed! Check your username/password and database.")
        print(f"Server said: {token_response.text}")
        return

    # Extract the VIP Badge from the response
    token = token_response.json().get("access_token")
    print("✅ Login successful! Got VIP Token.\n")

    # ==========================================
    # STEP 2: PREPARE THE IMAGE
    # ==========================================
    print("--- 2. Preparing the Image ---")
    try:
        with open(IMAGE_PATH, "rb") as image_file:
            raw_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        full_base64_string = f"data:image/png;base64,{raw_base64}"
        print("✅ Image loaded and converted to Base64.\n")
    except FileNotFoundError:
        print(f"❌ Could not find {IMAGE_PATH}. Please create a small drawing first!")
        return

    # ==========================================
    # STEP 3: ASK THE AI
    # ==========================================
    print("--- 3. Asking the AI ---")
    
    # The new, ultra-clean payload
    payload = {
        "base64_string": full_base64_string
    }
    
    # CRITICAL: Attach the JWT token to the HTTP Headers
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Send the request to the locked endpoint
    response = requests.post(
        f"{BASE_URL}/api/ai_guess/", 
        json=payload, 
        headers=headers
    )

    # ==========================================
    # STEP 4: PRINT THE RESULTS
    # ==========================================
    print(f"Status Code: {response.status_code}")
    try:
        # Print the beautiful JSON response
        print(json.dumps(response.json(), indent=4))
    except Exception:
        # If it crashes, print the raw error text
        print(response.text)

if __name__ == "__main__":
    test_ai_microservice()
import requests
import json

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing /ingest endpoint...")
    response = requests.post(f"{base_url}/ingest", json={"app_id": "demo_app_1"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    print("Testing /chat endpoint...")
    chat_payload = {
        "app_id": "demo_app_1",
        "question": "What is the company's remote work policy?"
    }
    response = requests.post(f"{base_url}/chat", json=chat_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_api()

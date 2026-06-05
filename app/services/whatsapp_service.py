import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERSION = "v20.0"

def send_whatsapp_message(to: str, text: str):
    """Sends a simple text message via WhatsApp Business API"""
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"[WA_SEND] Status: {response.status_code}, Body: {response.text}")
        return response.json()
    except Exception as e:
        print(f"[WA_SEND ERROR] Failed to send WhatsApp message: {e}")
        return {"error": str(e)}

def send_whatsapp_image(to: str, image_url: str, caption: str = ""):
    """Sends an image message via WhatsApp Business API"""
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"[WA_SEND_IMAGE] Status: {response.status_code}, Body: {response.text}")
        return response.json()
    except Exception as e:
        print(f"[WA_SEND_IMAGE ERROR] Failed to send WhatsApp image: {e}")
        return {"error": str(e)}

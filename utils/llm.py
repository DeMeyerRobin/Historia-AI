import os
import requests
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
HF_TOKEN = os.getenv("HF_API_KEY") 
MODEL = "Qwen/Qwen2.5-7B-Instruct" 

# Use the V1 Router endpoint (OpenAI Compatible)
API_URL = "https://router.huggingface.co/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

def generate(prompt: str, *, max_tokens: int = 500, temperature: float = 0.7):
    """Call the HF Router using the Chat Completion standard."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # Access the message content in the OpenAI-style response object
            return result['choices'][0]['message']['content']
        else:
            return f"❌ Error {response.status_code}: {response.text}"

    except Exception as e:
        return f"⚠️ Connection error: {str(e)}"

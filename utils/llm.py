import os
import aiohttp
import asyncio
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

async def generate(prompt: str, *, max_tokens: int = 500, temperature: float = 0.7):
    """Call the HF Router using the Chat Completion standard (async)."""
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
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(API_URL, headers=HEADERS, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    # Access the message content in the OpenAI-style response object
                    return result['choices'][0]['message']['content']
                else:
                    text = await response.text()
                    return f"❌ Error {response.status}: {text}"

    except asyncio.TimeoutError:
        return f"⚠️ Request timeout after 120 seconds"
    except Exception as e:
        return f"⚠️ Connection error: {str(e)}"

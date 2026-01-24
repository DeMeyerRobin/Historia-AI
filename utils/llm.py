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

async def generate(prompt: str, *, max_tokens: int = 500, temperature: float = 0.7, max_retries: int = 3):
    """Call the HF Router using the Chat Completion standard (async) with retry logic."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(API_URL, headers=HEADERS, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Access the message content in the OpenAI-style response object
                        return result['choices'][0]['message']['content']
                    elif response.status in [502, 503, 504]:  # Server errors - retry
                        text = await response.text()
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                            print(f"⚠️ Server error {response.status}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return f"❌ Error {response.status} after {max_retries} attempts: Server temporarily unavailable"
                    else:
                        text = await response.text()
                        # For other errors, don't retry
                        return f"❌ Error {response.status}: {text[:200]}"

        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️ Request timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(wait_time)
                continue
            return f"⚠️ Request timeout after {max_retries} attempts (120 seconds each)"
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️ Connection error: {str(e)}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(wait_time)
                continue
            return f"⚠️ Connection error after {max_retries} attempts: {str(e)}"
    
    return "❌ Max retries exceeded"

import os
import requests
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

key = os.getenv("GROQ_API_KEY")

if not key:
    raise ValueError("GROQ_API_KEY not found in .env")

# Send a minimal test request
response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}"},
    json={
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "Réponds juste : OK"}]
    },
    timeout=60,
)

print("Status:", response.status_code)

if response.status_code == 200:
    print("Response:", response.json()["choices"][0]["message"]["content"])
else:
    print("Error body:", response.text)

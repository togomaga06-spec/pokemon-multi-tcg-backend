import os
import base64
import json
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

@app.get("/")
def root():
    return {"status": "online", "message": "Multi-TCG API ready"}

@app.post("/analyze")
async def analyze_card(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "pixtral-12b-2409",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
Tu es un expert en cartes TCG (Pokémon, Yu-Gi-Oh, Magic).
Analyse l’image et renvoie un JSON STRICTEMENT au format suivant :

{
  "tcg": "...",
  "name": "...",
  "set": "...",
  "rarity": "...",
  "price_estimate": "...",
  "vinted_text": "...",
  "instagram_text": "..."
}

Ne renvoie rien d’autre que ce JSON.
"""
                    },
                    {
                        "type": "input_image",
                        "image": image_b64
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    try:
        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed
    except Exception:
        return {"error": "Invalid response from Mistral", "raw": result}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

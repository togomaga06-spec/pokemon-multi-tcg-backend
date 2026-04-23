import os
import base64
import json
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Autoriser Flutter / Web / Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clé API Mistral
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

@app.get("/")
def root():
    return {"status": "online", "message": "Multi-TCG API ready"}


@app.post("/analyze")
async def analyze_card(file: UploadFile = File(...)):
    # Lire l'image envoyée par Flutter
    image_bytes = await file.read()
    print("Taille image_bytes:", len(image_bytes))
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    print("Taille image_b64:", len(image_b64))


    # Endpoint Mistral
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prompt + image
    payload = {
        "model": "pixtral-12b",   # ✔ modèle correct
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
                        "image": image_b64   # ✔ format correct
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    # Appel API Mistral
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    # Extraction du JSON renvoyé par Mistral
    try:
        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed
    except Exception:
        return {
            "error": "Invalid response from Mistral",
            "raw": result
        }


# Render utilise une variable d'environnement PORT
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

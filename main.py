import os
import json
import requests
from fastapi import FastAPI, UploadFile, File, Form
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

# -----------------------------
# 1) UPLOAD IMAGE TO MISTRAL
# -----------------------------
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    image_bytes = await file.read()

    url = "https://api.mistral.ai/v1/files"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}

    files = {
        "file": (file.filename, image_bytes, file.content_type)
    }

    response = requests.post(url, headers=headers, files=files)
    result = response.json()

    if "id" not in result:
        return {"error": "Upload failed", "raw": result}

    return {"file_id": result["id"]}


# -----------------------------
# 2) ANALYZE IMAGE WITH PIXTRAL
# -----------------------------
@app.post("/analyze")
async def analyze_card(file_id: str = Form(...)):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "pixtral-12b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
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
                        "type": "file",
                        "file_id": file_id
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


# -----------------------------
# RUN LOCAL
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

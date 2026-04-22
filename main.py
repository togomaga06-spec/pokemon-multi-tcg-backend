from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import base64
import os
import requests

app = FastAPI()

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

    prompt = """
Tu es un expert en cartes TCG. Analyse l’image et renvoie un JSON structuré :

{
  "tcg": "Pokémon | Yu-Gi-Oh | Magic | One Piece | Lorcana | DBS | FAB | Autre",
  "nom": "Nom exact de la carte",
  "extension": "Nom ou code de l’extension",
  "rarete": "Rareté exacte",
  "description": "Description courte de la carte",
  "prix_estime": "Prix moyen sur le marché",
  "texte_vinted": "Texte optimisé pour vendre la carte",
  "texte_instagram": "Texte stylé pour poster la carte"
}

Si l’image est floue ou illisible, indique-le dans le JSON.
"""

    payload = {
        "model": "pixtral-12b-2409",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                ]
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return JSONResponse(content=data)

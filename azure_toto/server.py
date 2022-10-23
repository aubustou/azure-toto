from __future__ import annotations

import fastapi
import requests

app = fastapi.FastAPI()

@app.get("/create")
def create(template: str):
    content = requests.get(template).json()


    return content 



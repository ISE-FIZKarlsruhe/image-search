#!/usr/bin/env python3

import base64
from fastapi import FastAPI, Response, Request, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from typing import List, Annotated, Union, Any
import weaviate

client = weaviate.Client(url="http://localhost:8080")

if not client.is_ready():
    raise ConnectionError("Connection to weaviate cluster failed.")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def fetch_similar_images(image: bytes, k: int = 1) -> List[str]:
    base64_image = base64.b64encode(image).decode()

    sourceImage = {"image": base64_image}

    weaviate_results = (
        client.query.get("Image", ["image", "identifier"])
        .with_near_image(sourceImage, encode=False)
        .with_limit(k)
        .do()
    )

    images = weaviate_results["data"]["Get"]["Image"]

    base64_images = []
    for image in images:
        base64_data = image["image"]
        base64_images.append(base64_data)

    return base64_images


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/search")
async def search_similar_images(
    image: UploadFile, k: Annotated[int, Form()], request: Request
):
    content = await image.read()

    similar_images = fetch_similar_images(content, k)
    return templates.TemplateResponse(
        "results.html", {"request": request, "results": similar_images}
    )

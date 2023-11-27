#!/usr/bin/env python3

import base64
from dotenv import load_dotenv
from fastapi import FastAPI, Response, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
import os
from time import sleep
from typing import List, Annotated, Union, Any
import weaviate

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")


def initiate_weaviate_connection(url: str, retries: int = 10) -> weaviate.Client:
    try:
        client = weaviate.Client(url=WEAVIATE_URL)
        return client
    except weaviate.exceptions.WeaviateStartUpError as e:
        print("Connecting to weaviate server failed.")

        if retries == 0:
            print("Retries exceeded. Shutting down script!")
            raise ConnectionError("Connection to weaviate server failed.")

        print(f"Retrying in 5 seconds... ({retries - 1} retries left)\n")
        sleep(5)
        return initiate_weaviate_connection(url, retries=retries - 1)


client = initiate_weaviate_connection(url=WEAVIATE_URL)

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

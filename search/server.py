#!/usr/bin/env python3

import base64
from dotenv import load_dotenv
from fastapi import FastAPI, Response, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
import os
from time import sleep
from typing import List, Annotated, Union, Any, Tuple
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


def fetch_results(image: bytes, k: int = 1) -> List[Tuple[str, str]]:
    base64_image = base64.b64encode(image).decode()

    sourceImage = {"image": base64_image}

    weaviate_results = (
        client.query.get("Image", ["image", "subject", "identifier"])
        .with_near_image(sourceImage, encode=False)
        .with_limit(k)
        .do()
    )

    images = weaviate_results["data"]["Get"]["Image"]

    results = []
    for image in images:
        base64_data = image["image"]
        subject = image["subject"]

        results.append((base64_data, subject))

    return results


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/index-size")
def get_index_size():
    weaviate_response = client.query.aggregate("Image").with_meta_count().do()
    index_size = weaviate_response["data"]["Aggregate"]["Image"][0]["meta"]["count"]
    return {"index-size": index_size}


@app.post("/search")
async def search_similar_images(
    image: UploadFile, k: Annotated[int, Form()], request: Request
):
    content = await image.read()

    results = fetch_results(content, k)
    return templates.TemplateResponse(
        "results.html", {"request": request, "results": results}
    )

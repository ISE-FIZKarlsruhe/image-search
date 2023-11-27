#!/usr/bin/env python3

import base64
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from io import BytesIO
import json
import os
from time import sleep
from typing import List, Annotated, Union, Any
import weaviate
from zipfile import ZipFile

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

client.batch.configure(
    batch_size=10,
    dynamic=True,
    timeout_retries=3,
    callback=None,
)

if not client.is_ready():
    raise ConnectionError("Connection to weaviate cluster failed.")

schema = None
with open("schema.json") as json_file:
    schema = json.load(json_file)

try:
    client.schema.create(schema)
except weaviate.exceptions.UnexpectedStatusCodeException:
    pass


app = FastAPI()
templates = Jinja2Templates(directory="templates")


def index_images(zip_archive):
    with client.batch as batch:
        for zipinfo in zip_archive.filelist:
            file_name = zipinfo.filename

            if file_name[-4:] not in [".png", ".jpg", "jpeg"]:
                continue

            image = zip_archive.read(file_name)
            base64_image = base64.b64encode(image).decode()

            data = {"image": base64_image, "identifier": file_name}

            batch.add_data_object(data, "Image")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "show_success": False}
    )


@app.post("/index")
async def run_indexing(
    images: UploadFile, background_tasks: BackgroundTasks, request: Request
):
    content = await images.read()
    zip_archive = ZipFile(BytesIO(content))

    background_tasks.add_task(index_images, zip_archive)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "show_success": True, "file_name": images.filename},
    )

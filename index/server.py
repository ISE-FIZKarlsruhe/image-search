#!/usr/bin/env python3

import base64
from io import BytesIO
import json
from fastapi import FastAPI, Response, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from typing import List, Annotated, Union, Any
import weaviate
from zipfile import ZipFile

client = weaviate.Client(url="http://localhost:8080")
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


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/index")
async def index_images(images: UploadFile, request: Request):
    content = await images.read()
    zip_archive = ZipFile(BytesIO(content))

    with client.batch as batch:

        for zipinfo in zip_archive.filelist:
            file_name = zipinfo.filename

            if file_name[-4:] not in [".png", ".jpg", "jpeg"]:
                print("Unsupported file type:", file_name)
                continue

            image = zip_archive.read(file_name)
            base64_image = base64.b64encode(image).decode()

            data = {"image": base64_image, "identifier": file_name}

            batch.add_data_object(data, "Image")


    return 200

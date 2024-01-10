#!/usr/bin/env phython3

import base64
from dotenv import load_dotenv
import os
import weaviate


load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
COMPARISON_IMAGE_PATH = os.getenv("COMPARISON_IMAGE_PATH")

client = weaviate.Client(url=WEAVIATE_URL)

with open(COMPARISON_IMAGE_PATH, "rb") as image_file:
    image = image_file.read()
    base64_image = base64.b64encode(image).decode()

    sourceImage = {"image": base64_image}

    weaviate_results = (
        client.query.get("Image", ["image", "subject", "identifier"])
        .with_near_image(sourceImage, encode=False)
        .with_limit(2)
        .do()
    )

    images = weaviate_results["data"]["Get"]["Image"]
    image = images[0]

    base64_data = image["image"]
    file_name = image["identifier"]

    file_path = f"tmp/{file_name}"
    with open(file_path, "wb") as fh:
        fh.write(base64.decodebytes(bytes(base64_data, "utf-8")))

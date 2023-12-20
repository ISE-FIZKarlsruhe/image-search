#!/usr/bin/env python3

import base64
import json
from dotenv import load_dotenv
import os
from tqdm import tqdm
import weaviate

from utils.weaviate_ import initiate_weaviate_connection


load_dotenv()

SEED_DATA_DIR = os.getenv("SEED_DATA_DIR")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")

client = initiate_weaviate_connection(url=WEAVIATE_URL)

schema = None
with open("schema.json") as json_file:
    schema = json.load(json_file)

try:
    client.schema.create(schema)
except weaviate.exceptions.UnexpectedStatusCodeException:
    pass


client.batch.configure(
    batch_size=10,
    dynamic=True,
    timeout_retries=3,
    callback=None,
)

with client.batch as batch:
    for i, file_name in tqdm(enumerate(os.listdir(SEED_DATA_DIR))):
        if file_name[-4:] not in [".png", ".jpg", "jpeg"]:
            print("Unsupported file type:", file_name)
            continue

        file_path = f"{SEED_DATA_DIR}/{file_name}"
        with open(file_path, "rb") as image_file:
            image = image_file.read()
            base64_image = base64.b64encode(image).decode()

            data = {"image": base64_image, "identifier": file_name}

            batch.add_data_object(data, "Image")

#!/usr/bin/env python3

import base64
import json
from dotenv import load_dotenv
import os
import re
import requests
from tqdm import tqdm
import weaviate

from utils.weaviate_ import initiate_weaviate_connection


load_dotenv()

SEED_DATA_URL = os.getenv("SEED_DATA_LIST_URL")
SEED_DATA_BASE_URL = os.getenv("SEED_DATA_BASE_URL")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")

response = requests.get(url=SEED_DATA_URL)
directory_listing_html = response.text

matches = re.findall(r" href=\".*\"", directory_listing_html)
image_ids = [match[7:-1] for match in matches]

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
    for i, image_id in tqdm(enumerate(image_ids)):
        if i > 5000:
            break

        image_link = image_id

        if SEED_DATA_BASE_URL is not None:
            image_link = f"{SEED_DATA_BASE_URL}/{image_link}"

        try:
            response = requests.get(image_link)
            content_type = response.headers["content-type"]

            if not content_type.startswith("image/"):
                continue

            image = response.content
            base64_image = base64.b64encode(image).decode()

            data = {"image": base64_image, "identifier": image_id}

            batch.add_data_object(data, "Image")

        except Exception as e:
            print(str(e))

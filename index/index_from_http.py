#!/usr/bin/env python3

import base64
import json
from dotenv import load_dotenv
import os
import re
import requests
from tqdm import tqdm
from typing import Dict
import weaviate

from utils.weaviate_ import initiate_weaviate_connection


def get_subject(file_name: str, subject_mapping: Dict) -> str:
    if "." in file_name and len(file_name.split(".")[-1]) <= 4:
        file_name_components = file_name.split(".")
        file_name = ".".join(file_name_components[:-1])

    if file_name in subject_mapping:
        return subject_mapping[file_name]
    else:
        return "N/A"


load_dotenv()

SEED_DATA_URL = os.getenv("SEED_DATA_LIST_URL")
SEED_DATA_BASE_URL = os.getenv("SEED_DATA_BASE_URL")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
SUBJECT_DICT_TARGET_PATH = os.getenv("SUBJECT_DICT_TARGET_PATH")

subject_mapping: Dict = json.load(open(SUBJECT_DICT_TARGET_PATH))

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

            subject = get_subject(image_id, subject_mapping)

            data = {
                "image": base64_image,
                "subject": subject,
                "fileName": image_id,
                "identifier": image_id,
            }

            batch.add_data_object(data, "Image")

        except Exception as e:
            print(str(e))

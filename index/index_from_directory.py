#!/usr/bin/env python3

import base64
from dotenv import load_dotenv
import json
import os
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

SEED_DATA_DIR = os.getenv("SEED_DATA_DIR")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
SUBJECT_DICT_TARGET_PATH = os.getenv("SUBJECT_DICT_TARGET_PATH")

subject_mapping: Dict = None
with open(SUBJECT_DICT_TARGET_PATH) as subject_mapping_file:
    subject_mapping = json.load(subject_mapping_file)

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

        subject = get_subject(file_name, subject_mapping)

        file_path = f"{SEED_DATA_DIR}/{file_name}"
        with open(file_path, "rb") as image_file:
            image = image_file.read()
            base64_image = base64.b64encode(image).decode()

            data = {
                "image": base64_image,
                "subject": subject,
                "fileName": file_name,
                "identifier": file_name,
            }

            batch.add_data_object(data, "Image")

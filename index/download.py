#!/usr/bin/env python3

from dotenv import load_dotenv
import json
import os
import requests
from tqdm import tqdm

"""
Reads in a file full of iiif manifest links, extracts the 
corresponding images, and downloads them.
"""

load_dotenv()

IIIF_PATH = "./data/example_iiif"
DOWNLOAD_TARGET_PATH = os.getenv("SEED_DATA_DIR")

manifest_links = []
with open(IIIF_PATH) as iiif_link_file:
    for link in iiif_link_file.readlines():
        if link.endswith("\n"):
            link = link[:-1]

        manifest_links.append(link)

decode_error_count = 0

image_base_links = []
for manifest_link in tqdm(manifest_links):
    try:
        response = requests.get(url=manifest_link)
        data = response.json()
    except json.decoder.JSONDecodeError as e:
        decode_error_count += 1
        continue

    try:
        sequences = data["sequences"]
        for sequence in sequences:
            canvases = sequence["canvases"]
            for canvas in canvases:
                images = canvas["images"]
                for image in images:
                    image_id = image["resource"]["service"]["@id"]

                    image_base_links.append(image_id)

    except Exception as e:
        pass

print(
    f"Failed to decode {decode_error_count} manifest links from {len(manifest_links)} provided manifest links ({100 * round(decode_error_count / len(manifest_links), 2)} %)"
)

image_links = []
for image_base_link in image_base_links:
    image_link = f"{image_base_link}/full/256,/0/default.jpg"
    image_links.append(image_link)

if not os.path.exists(DOWNLOAD_TARGET_PATH):
    os.makedirs(DOWNLOAD_TARGET_PATH)

for image_link in tqdm(image_links):
    link_components = image_link.split("/")
    image_identifier = "_".join(link_components[-5:])
    target_path = f"{DOWNLOAD_TARGET_PATH}/{image_identifier}"

    image_data = requests.get(image_link).content
    with open(target_path, "wb") as target_file:
        target_file.write(image_data)

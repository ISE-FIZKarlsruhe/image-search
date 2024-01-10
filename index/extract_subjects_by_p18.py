#!/usr/bin/env python3

import json
import os
from typing import List
from urllib.parse import unquote


def split_into_components(line: str) -> List[str]:
    raw_components = line.split(" ")

    components: List[str] = []

    components_to_merge = []
    for component in raw_components:
        if '"' in component and len(components_to_merge) == 0:
            components_to_merge.append(component)
        elif '"' in component and len(components_to_merge) > 0:
            merged_component = " ".join(components_to_merge)
            components.append(merged_component)
            components_to_merge = []
        elif len(components_to_merge) > 0:
            components_to_merge.append(component)
        else:
            components.append(component)

    return components


def extract_file_name(raw_url: str) -> str:
    raw_url = raw_url.replace("<", "")
    raw_url = raw_url.replace(">", "")

    url = unquote(raw_url)

    url_components = url.split("/")
    file_name = url_components[-1]

    if "." in file_name and len(file_name.split(".")[-1]) <= 4:
        file_name_components = file_name.split(".")
        file_name = ".".join(file_name_components[:-1])

    return file_name


if __name__ == "__main__":
    TTL_DATA_DIR = os.getenv("TTL_DATA_DIR")
    SUBJECT_DICT_TARGET_PATH = os.getenv("SUBJECT_DICT_TARGET_PATH")

    assert SUBJECT_DICT_TARGET_PATH.endswith(".json")

    subject_dict = {}
    for file_name in os.listdir(TTL_DATA_DIR):
        if not file_name.endswith(".ttl"):
            continue

        file_path = f"{TTL_DATA_DIR}/{file_name}"

        with open(file_path) as ttl_file:
            last_encountered_subject: str = None
            for i, line in enumerate(ttl_file):
                if line.startswith("@prefix"):
                    continue

                components = split_into_components(line)

                if len(components) < 3:
                    continue

                if len(components) == 4:
                    subject, predicate, object, eol = components
                    last_encountered_subject = subject

                if len(components) == 3:
                    predicate, object, eol = components

                if not predicate.endswith("P18"):
                    continue

                file_name = extract_file_name(object)

                subject_dict[file_name] = last_encountered_subject

    with open(SUBJECT_DICT_TARGET_PATH, "w") as target_file:
        json.dump(subject_dict, target_file)

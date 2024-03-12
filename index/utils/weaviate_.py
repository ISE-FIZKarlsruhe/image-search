#!/usr/bin/env python3

from time import sleep
import weaviate


def initiate_weaviate_connection(url: str, retries: int = 10) -> weaviate.Client:
    try:
        client = weaviate.Client(url=url)
        print("Successfully connected to weaviate client.")
        return client
    except weaviate.exceptions.WeaviateStartUpError as e:
        print("Connecting to weaviate server failed.")

        if retries == 0:
            print("Retries exceeded. Shutting down script!")
            raise ConnectionError("Connection to weaviate server failed.")

        print(f"Retrying in 5 seconds... ({retries - 1} retries left)\n")
        sleep(5)
        return initiate_weaviate_connection(url, retries=retries - 1)

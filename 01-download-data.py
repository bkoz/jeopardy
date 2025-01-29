#
# Experiment with Weaviate Demo Data
#
# https://github.com/databyjp/wv_demo_uploader.git
#
# Work in Progress!

import weaviate_datasets as wd
import weaviate
import os
import logging
import requests
import json

def semantic_search(collection:weaviate.collections.Collection, query: str)-> dict:

    response = collection.query.near_text(
        query=query,
        limit=1
    )
    return response.objects[0].properties


def generative_search(collection:weaviate.collections.Collection, query: str,
                      task='Summarize', limit=1)-> dict:
    response = collection.generate.near_text(
        query=query,
        limit=1,
        grouped_task=task
    )
    return response.generated

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.info('Hello Weaviate')

huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
if huggingface_api_key == None:
     logging.error('HUGGINGFACE_API_KEY not set!')
     exit(1)

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key == None:
     logging.error('OPENAI_API_KEY not set!')
     exit(1)

client = weaviate.connect_to_embedded(
    headers={"X-OpenAI-Api-Key": openai_api_key,
             "X-Huggingface-Api-Key": huggingface_api_key}
)
client.collections.delete_all()

dataset = wd.JeopardyQuestions1k()  # Instantiate dataset
dataset.upload_dataset(client)  # Pass the Weaviate client instance

collections = client.collections.list_all()

collection = client.collections.get('JeopardyQuestion')
logging.info(semantic_search(collection=collection, query='guitar'))
logging.info(generative_search(collection=collection, query='guitar',
                      task='Summarize', limit=1))
collection = client.collections.get('JeopardyCategory')
logging.info(semantic_search(collection=collection, query='guitar'))

# logging.info('*** GET ***')
# logging.info(client.collections.get)

client.close()

logging.info('Finished!')
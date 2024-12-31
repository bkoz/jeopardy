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

def respond(collection, query):

    response = collection.query.near_text(
        query=query,
        limit=1
    )
    return response.objects[0].properties

logging.basicConfig(encoding='utf-8', level=logging.INFO)

logging.info('Weaviate')

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
print('***************')
print(collections)
print('***************')

collection = client.collections.get('JeopardyQuestion')
print('***************')
print(respond(collection=collection, query='guitar'))
print('***************')

# logging.info('*** GET ***')
# logging.info(client.collections.get)

client.close()

logging.info('Finished!')
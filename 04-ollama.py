import weaviate
import weaviate.classes as wvc
from  weaviate.classes.config import Configure
from weaviate.classes.init import Auth
import requests, json
import logging
import os

# Set up logging
logging.basicConfig(encoding='utf-8', level=logging.INFO)
logging.info('Weaviate')

weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
ollama_api_endpoint = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_vectorizer_model = model = os.getenv("OLLAMA_VECTORIZER", "all-minilm")
ollama_generative_model = os.getenv("OLLAMA_LLM","qwen3:4b")

# Check if the environment variables are set
if weaviate_api_key == None:
     logging.error('WEAVIATE_KEY not set!')
     exit(1)

# client = weaviate.connect_to_embedded(
#     # version="1.26.1",
#     headers={
#         "X-Huggingface-Api-Key": huggingface_api_key,
#         "X-OpenAI-Api-Key": openai_api_key
#     }
# )

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="pa3ddmygtnaokakprvcxyg.c0.us-west3.gcp.weaviate.cloud",
    auth_credentials=Auth.api_key(weaviate_api_key),
)

if client.is_ready():
    logging.info('')
    logging.info(f'Found {len(client.cluster.nodes())} Weaviate nodes.')
    logging.info('')
    for node in client.cluster.nodes():
        logging.info(node)
        logging.info('')
    logging.info(f'metadata = {client.get_meta()}')

resp = requests.get(
    "https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json"
)
data = json.loads(resp.text)
client.collections.delete_all()

# ===== Define the collection =====
questions = client.collections.create(
    name="Question",
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_weaviate(),
    generative_config=wvc.config.Configure.Generative.ollama(
        api_endpoint=ollama_api_endpoint,
        model=ollama_generative_model
    )
)

questions = client.collections.get("Question")

with questions.batch.fixed_size(batch_size=10) as batch:
    for d in data:
        batch.add_object(
            {
                "category": d["Category"],
                "question": d["Question"],
                "answer": d["Answer"],
            }
        )
        if batch.number_errors > 10:
            logging.error("Batch import stopped due to excessive errors.")
            break

failed_objects = questions.batch.failed_objects
if failed_objects:
    logging.error(f"Number of failed imports: {len(failed_objects)}")
    logging.error(f"First failed object: {failed_objects[0]}")
else:
    logging.info("All objects imported successfully.")

client.close()  # Free up resources
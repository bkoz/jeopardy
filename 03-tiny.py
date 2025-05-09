import weaviate
# import weaviate.classes as wvc
from  weaviate.classes.config import Configure
from weaviate.classes.init import Auth
import requests, json
import logging
import os

# Set up logging
logging.basicConfig(encoding='utf-8', level=logging.INFO)
logging.info('Weaviate')

huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Check if the environment variables are set
if openai_api_key == None:
     logging.error('OPENAI_API_KEY not set!')
     exit(1)
if huggingface_api_key == None:
     logging.error('HUGGINGFACE_API_KEY not set!')
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
    auth_credentials=Auth.api_key(os.environ["WEAVIATE_KEY"]),
    headers = {
        "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
        "X-HuggingFace-Api-Key": os.environ["HUGGINGFACE_API_KEY"]
    }
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
# questions = client.collections.create(
#     "Question",
#     vectorizer_config=Configure.Vectorizer.text2vec_huggingface(wait_for_model=True,
#     model="sentence-transformers/all-MiniLM-L6-v2",
#     # name="title_vector",
#     source_properties=["title"],                                                            ),  
#     # generative_config=wvc.config.Configure.Generative.openai()  
# )

questions = client.collections.create(
    "Question",
    vectorizer_config=[
        Configure.NamedVectors.text2vec_huggingface(
            name="title_vector",
            source_properties=["title"],
            # NOTE: Use only one of (`model`), (`passage_model` and `query_model`), or (`endpoint_url`)
            model="sentence-transformers/all-MiniLM-L6-v2",
            # passage_model="sentence-transformers/facebook-dpr-ctx_encoder-single-nq-base",    # Required if using `query_model`
            # query_model="sentence-transformers/facebook-dpr-question_encoder-single-nq-base", # Required if using `passage_model`
            # endpoint_url="<custom_huggingface_url>",
            #
            wait_for_model=True,
            # use_cache=True,
            # use_gpu=True,
        )
    ],
    # Additional parameters not shown
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
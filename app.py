import gradio as gr
from huggingface_hub import InferenceClient
import logging
import os
import requests
import json
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
import weaviate.classes as wvc

logging.basicConfig(level=logging.INFO)

weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
ollama_api_endpoint = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_vectorizer_model = model = os.getenv("OLLAMA_VECTORIZER", "all-minilm")
ollama_generative_model = os.getenv("OLLAMA_LLM","qwen3:4b")

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

client.collections.delete("Question")

questions = client.collections.create(
    name="Question",
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_weaviate(),
    generative_config=wvc.config.Configure.Generative.ollama(
        api_endpoint=ollama_api_endpoint,
        model=ollama_generative_model
    )
)
resp = requests.get('https://raw.githubusercontent.com/databyjp/wv_demo_uploader/main/weaviate_datasets/data/jeopardy_1k.json')

data = json.loads(resp.text)

question_objs = list()
for i, d in enumerate(data):
    question_objs.append({
        "answer": d["Answer"],
        "question": d["Question"],
        "category": d["Category"],
        "air_date": d["Air Date"],
        "round": d["Round"],
        "value": d["Value"]
})

logging.info('Importing 1000 Questions...')
questions.data.insert_many(question_objs)
logging.info('Finished Importing Questions')
print(questions)

def respond(query):

    response = questions.query.near_text(
        query=query,
        limit=1
    )

    return response.objects[0].properties 

with gr.Blocks(title="Search the Jeopardy Vector Database powered by Weaviate") as demo:
            gr.Markdown("""# Search the Jeopardy Vector Database powered by Weaviate""")
            semantic_examples = [
                ["Nature"],
                ["Music"],
                ["Wine"],
                ["Consumer Products"],
                ["Sports"],
                ["Fishing"],
                ["Food"],
                ["Weather"]
            ]
            semantic_input_text = gr.Textbox(label="Enter a search concept or choose an example below:", value=semantic_examples[0][0])
            gr.Examples(semantic_examples, inputs=semantic_input_text, label="Example search concepts:")
            vdb_button = gr.Button(value="Search the Jeopardy Vector Database.")
            vdb_button.click(fn=respond, inputs=[semantic_input_text], outputs=gr.Textbox(label="Search Results"))
            

if __name__ == "__main__":
    demo.launch()


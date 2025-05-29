import gradio as gr
import logging
import os
import time
import requests
import json
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
import weaviate.classes as wvc
from weaviate.embedded import EmbeddedOptions
from weaviate.config import AdditionalConfig, Timeout

logging.basicConfig(level=logging.INFO)

weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
ollama_api_endpoint = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_vectorizer_model = model = os.getenv("OLLAMA_VECTORIZER", "all-minilm")
ollama_generative_model = os.getenv("OLLAMA_LLM","qwen3:4b")

client = weaviate.connect_to_embedded(
     environment_variables={
          "ENABLE_MODULES": "text2vec-ollama,generative-ollama"
     },
     additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=1000, insert=120))
)

if client.is_ready():
    logging.info('')
    logging.info(f'Found {len(client.cluster.nodes())} Weaviate nodes.')
    logging.info('')
    for node in client.cluster.nodes():
        logging.info(node)
        logging.info('')
    logging.info(client.get_meta())

# Delete the Question collection if it exists.
if client.collections.exists("Question"):
    client.collections.delete("Question")

questions = client.collections.create(
    name="Question",
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(
         api_endpoint=ollama_api_endpoint,
         model=ollama_vectorizer_model
    ),
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

logging.debug(questions)

def respond(query, limit=1) -> str:

    response = questions.query.near_text(
        query=query,
        limit=limit,
    )

    return response.objects[0].properties 

def generative_search(query='computers', task=None, limit=1) -> str:
    print(f'\nPerforming generative search, query = {query}, limit = {limit}.')
    print(f'Prompt: {task}')
    print(f'limit = {limit}')
    start_time = time.time()
    response = questions.generate.near_text(
        query=query,
        limit=limit,
        grouped_task=task
    )
    print(f'Elapsed time = {time.time() - start_time} seconds')
    return response.generated

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
            limit_slider = gr.Slider(label="Adjust the query return limit. (Optional)",value=1, minimum=1, maximum=5, step=1)
            vdb_button.click(fn=respond, inputs=[semantic_input_text, limit_slider], outputs=gr.Textbox(label="Search Results"))
            
            #
            # Generative Search 
            # 
            prompt_examples = [
                ["Summarize the information."],
                ["Summarize the information for a child using emojis."]
            ]

            gr.Markdown("""### Summarize""")
            generative_search_prompt_text = gr.Textbox(label="Enter a summarization task or choose an example below.", value=prompt_examples[0][0])
            gr.Examples(prompt_examples,
                fn=generative_search,
                inputs=[generative_search_prompt_text]
            )
            button = gr.Button(value="Generate the summary.")
            button.click(fn=generative_search,
            inputs=[semantic_input_text, generative_search_prompt_text, limit_slider],
            outputs=gr.Textbox(label="Summary"))
            

if __name__ == "__main__":
    demo.launch()


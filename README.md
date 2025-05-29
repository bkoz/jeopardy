# Jeopardy
- A simple summarization RAG example that imports 1000 Jeopardy questions.
  - Uses Weaviate's [embedded server](https://weaviate.io/developers/weaviate/connections/connect-embedded)
- [Runs local ollama](https://github.com/prulloac/devcontainer-features/tree/main/src/ollama) in the codespace devcontainer to serve the embedding model and LLM.

Model server checks

```bash
curl localhost:11434/api/tags | jq
```

Embeddings

```bash
curl http://localhost:11434/api/embed -d '{
  "model": "all-minilm",
  "input": "hello"
}'
```

Completion
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Hello", "stream": false
}'
```

### Requirements
- Github codespace with 8 cores and 32GB of memory.

# config.py
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain import hub
from langchain_core.vectorstores import InMemoryVectorStore

# LLM (Ollama must be running locally)
llm = OllamaLLM(model="llama3.1:8b", base_url="http://localhost:11434")

# Embeddings: try Ollama embeddings, fallback to HuggingFace
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
except Exception:
    # fallback (requires sentence-transformers / huggingface installation)
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Simple in-memory vector store (good for testing)
vector_store = InMemoryVectorStore(embeddings)

# Load a RAG prompt from the hub
prompt = hub.pull("rlm/rag-prompt")

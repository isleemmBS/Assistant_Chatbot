# index.py -- run this once (or whenever you update indexed documents)
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import vector_store

loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(class_=("post-content", "post-title", "post-header"))
    ),
)

docs = loader.load()

# Split into manageable chunks with overlap
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
all_splits = text_splitter.split_documents(docs)

# OPTIONAL: attach metadata (useful for filtering)
for doc in all_splits:
    doc.metadata.setdefault("source", "https://lilianweng.github.io/posts/2023-06-23-agent/")
    # If your loader provides start_index you can compute a pseudo-page:
    if "start_index" in doc.metadata:
        doc.metadata.setdefault("page", int(doc.metadata["start_index"] // 1000) + 1)

# Add to vector store
vector_store.add_documents(all_splits)
print(f"Indexed {len(all_splits)} chunks.")

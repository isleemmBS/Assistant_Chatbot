from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings

# Load your PDF
pdf_path = "C:/Users/bensa/Desktop/courses/computer_vision/ch1_camera_model.pdf"
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = text_splitter.split_documents(documents)

# Create embeddings using Ollama
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Create a local Chroma database
db = Chroma.from_documents(docs, embeddings, persist_directory="./course_db")

# Save the database locally
db.persist()
print("✅ Course embeddings saved locally!")

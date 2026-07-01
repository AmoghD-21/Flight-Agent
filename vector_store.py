import os
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from ingest import process_air_india_docs

load_dotenv()


def build_vector_db():

    # 1. Load chunks
    chunks = process_air_india_docs()
    if not chunks:
        print("❌ No chunks found to embed.")
        return

    # 2. Get Hugging Face token from .env
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")

    if not hf_token:
        raise ValueError("Hugging Face token not found in .env file")

    # 3. Load Qwen embedding model
    print("🤖 Loading Qwen embedding model...")

    embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

    # 4. Build FAISS index
    print("🧠 Building FAISS vector store...")

    db = FAISS.from_documents(chunks, embeddings)

    # 5. Save locally
    db.save_local("faiss_index")

    print("💾 Vector store saved successfully!")


if __name__ == "__main__":
    build_vector_db()
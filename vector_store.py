import os
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingest import process_air_india_docs, extract_clean_pdf_content

load_dotenv()

DB_FOLDER = "faiss_index"


def get_embeddings():
    """Returns the embedding model used throughout the project."""

    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_vector_db():
    """Creates the FAISS database from scratch."""

    chunks = process_air_india_docs()

    if not chunks:
        print("❌ No chunks found.")
        return

    print("🤖 Loading embedding model...")
    embeddings = get_embeddings()

    print("🧠 Building FAISS index...")
    db = FAISS.from_documents(chunks, embeddings)

    db.save_local(DB_FOLDER)

    print("✅ Vector database created successfully!")


def add_new_pdf_to_vector_db(pdf_path):
    """
    Parses one uploaded PDF and appends it to the existing FAISS index.
    """

    print(f"\n📄 Processing {pdf_path}")

    pages = extract_clean_pdf_content(pdf_path)

    if not pages:
        return "❌ No text extracted."

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
    )

    chunks = splitter.split_documents(pages)

    embeddings = get_embeddings()

    if os.path.exists(DB_FOLDER):
        print("📚 Loading existing FAISS index...")
        db = FAISS.load_local(
            DB_FOLDER,
            embeddings,
            allow_dangerous_deserialization=True,
        )

        db.add_documents(chunks)

    else:
        print("📚 Creating new FAISS index...")
        db = FAISS.from_documents(chunks, embeddings)

    db.save_local(DB_FOLDER)

    return (
        f"✅ Successfully added "
        f"{os.path.basename(pdf_path)} "
        f"({len(chunks)} chunks)"
    )


if __name__ == "__main__":
    build_vector_db()



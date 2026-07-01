import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

def test_retriever():
    gh_token=os.getenv("GITHUB_TOKEN")
    if not gh_token:
        raise ValueError("GITHUB_TOKEN is not there")
    
    db_folder = "faiss_index"
    if not os.path.exists(db_folder):
        print(f"❌ Error: Database folder '{db_folder}' not found. Please run vector_store.py first.")
        return
    
    embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
    
    print("📂 Loading local FAISS vector store...")

    db = FAISS.load_local(db_folder, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})

    user_query = "What happens if a travel aclgent processes a refund against a different Form of Payment than original?"

    print(f"\n🔍 Searching database for: '{user_query}'...\n")
    relevant_docs = retriever.invoke(user_query)

    print(f"✨ Found {len(relevant_docs)} highly relevant matches:")
    print("=" * 60)

    for i, doc in enumerate(relevant_docs, 1):

        source = doc.metadata.get('source', 'Unknown')
        page = doc.metadata.get('page', 'Unknown')
        print(f"📄 Match #{i} | Source: {source} (Page {page})")
        print("-" * 60)
        # Printing the first 500 characters of the chunk
        print(doc.page_content[:600] + "\n...")
        print("=" * 60)


if __name__ == "__main__":
    test_retriever()

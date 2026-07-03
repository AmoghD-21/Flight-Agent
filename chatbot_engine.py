# import os
# from dotenv import load_dotenv

# from langchain_openai import ChatOpenAI
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings

# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.runnables import RunnableLambda

# load_dotenv()


# def initialize_chatbot():
#     gh_token = os.getenv("GITHUB_TOKEN")
#     if not gh_token:
#         raise ValueError("GITHUB_TOKEN is not set in environment variables")

#     # ---------------------------
#     # 1. Embeddings + Vector DB
#     # ---------------------------
#     embeddings = HuggingFaceEmbeddings(
#         model_name="BAAI/bge-base-en-v1.5",
#         model_kwargs={"device": "cpu"},
#         encode_kwargs={"normalize_embeddings": True},
#     )

#     db = FAISS.load_local(
#         "faiss_index",
#         embeddings,
#         allow_dangerous_deserialization=True
#     )

#     retriever = db.as_retriever(search_kwargs={"k": 4})

#     # ---------------------------
#     # 2. LLM
#     # ---------------------------
#     llm = ChatOpenAI(
#         model="gpt-4o",
#         api_key=gh_token,
#         base_url="https://models.inference.ai.azure.com",
#         temperature=0.2,
#     )

#     # ---------------------------
#     # 3. QUESTION REWRITER (replacement for history-aware retriever)
#     # ---------------------------
#     def rewrite_question(inputs):
#         question = inputs["input"]
#         chat_history = inputs["chat_history"]

#         messages = [
#             ("system",
#              "Rewrite the user question into a standalone question "
#              "using chat history if needed. Do NOT answer."),
#             MessagesPlaceholder("chat_history"),
#             ("human", "{input}")
#         ]

#         prompt = ChatPromptTemplate.from_messages(messages)

#         chain = prompt | llm

#         result = chain.invoke({
#             "input": question,
#             "chat_history": chat_history
#         })

#         return result.content

#     question_rewriter = RunnableLambda(rewrite_question)

#     # ---------------------------
#     # 4. RETRIEVAL STEP
#     # ---------------------------
#     def retrieve_docs(inputs):
#         question = inputs["rewritten_question"]
#         docs = retriever.invoke(question)
#         return docs

#     retriever_chain = RunnableLambda(retrieve_docs)

#     # ---------------------------
#     # 5. FINAL ANSWER PROMPT
#     # ---------------------------
#     system_prompt = """
# You are 'Maharaja AI', an expert automated corporate support assistant for Air India.

# Answer ONLY using the provided context.

# Context:
# {context}

# Rules:
# - Be accurate and professionalpython -c "import ragas.metrics.collections as c; print(dir(c))"
# - If answer is not in context, say:
#   "I am sorry, I cannot find that information in the official Air India policy documents."
# - Use markdown for tables if needed.
# """

#     qa_prompt = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         MessagesPlaceholder("chat_history"),
#         ("human", "{input}")
#     ])

#     # combine docs into text
#     def format_docs(docs):
#         return "\n\n".join(doc.page_content for doc in docs)

#     # final answer chain
#     def answer_chain(inputs):
#         context = format_docs(inputs["docs"])

#         chain = qa_prompt | llm

#         result = chain.invoke({
#             "context": context,
#             "input": inputs["input"],
#             "chat_history": inputs["chat_history"]
#         })

#         return {"answer": result.content,
#                 "context": inputs["docs"],
#                 "context_text": context 
#                 }

#     answer_runnable = RunnableLambda(answer_chain)

#     # ---------------------------
#     # 6. FULL PIPELINE (LCEL STYLE)
#     # ---------------------------
#     def pipeline(inputs):
#         question = question_rewriter.invoke(inputs)

#         docs = retriever_chain.invoke({
#             "rewritten_question": question
#         })

#         return answer_runnable.invoke({
#             "docs": docs,
#             "input": inputs["input"],
#             "chat_history": inputs["chat_history"]
#         })

#     rag_chain = RunnableLambda(pipeline)

#     return rag_chain


# # ---------------------------
# # CLI TEST LOOP
# # ---------------------------
# if __name__ == "__main__":
#     print("🤖 Initializing Maharaja AI (LangChain 1.3.11)...")
#     bot = initialize_chatbot()
#     chat_history = []

#     print("\n🎉 Ready! Type 'exit' to quit.\n")

#     while True:
#         user_input = input("You: ")

#         if user_input.lower() == "exit":
#             break

#         if not user_input.strip():
#             continue

#         response = bot.invoke({
#             "input": user_input,
#             "chat_history": chat_history
#         })

#         print(f"\nAI: {response['answer']}\n")
#         print("-" * 40)

#         chat_history.extend([
#             ("human", user_input),
#             ("ai", response["answer"])
#         ])











import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, AIMessage

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.documents import Document

load_dotenv()

# Safe conditional import of Streamlit to clear Pylance validation errors
try:
    import streamlit as st
except ImportError:
    st = None


def initialize_chatbot():
    # Retrieve token safely from Streamlit Cloud Secrets or fallback to local environment variables
    if st is not None and hasattr(st, "secrets"):
        gh_token = st.secrets.get("GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    else:
        gh_token = os.getenv("GITHUB_TOKEN")

    if not gh_token:
        raise ValueError("GITHUB_TOKEN is not set in environment variables or cloud secrets")

    # ---------------------------
    # 1. Embeddings + Self-Healing Vector DB
    # ---------------------------
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    index_path = "faiss_index"
    if os.path.exists(index_path) and os.path.exists(os.path.join(index_path, "index.faiss")):
        db = FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        # Cloud-safe fail-safe fallback path
        placeholder_doc = [Document(page_content="Air India Knowledge Base initialized. Please ingest documents via admin panel.", metadata={"source": "System Root"})]
        db = FAISS.from_documents(placeholder_doc, embeddings)
        db.save_local(index_path)

    retriever = db.as_retriever(search_kwargs={"k": 4})

    # ---------------------------
    # 2. LLM Configuration
    # ---------------------------
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=gh_token,
        base_url="https://models.inference.ai.azure.com",
        temperature=0.2,
    )

    # ---------------------------
    # 3. QUESTION REWRITER (Robust Message Object Normalizer)
    # ---------------------------
    def rewrite_question(inputs):
        question = inputs["input"]
        chat_history = inputs["chat_history"]

        # Safely parse text tuples or message objects into true LangChain shape formats
        processed_history = []
        for msg in chat_history:
            if isinstance(msg, tuple):
                role, content = msg
                if role in ["human", "user"]:
                    processed_history.append(HumanMessage(content=content))
                else:
                    processed_history.append(AIMessage(content=content))
            else:
                processed_history.append(msg)

        messages = [
            ("system",
             "Given a chat history and the latest user question which might reference context in the chat history, "
             "formulate a standalone question which can be understood without the chat history. Do NOT answer the question, "
             "just reformulate it if needed and otherwise return it as is."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]

        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm

        result = chain.invoke({
            "input": question,
            "chat_history": processed_history
        })

        return result.content

    question_rewriter = RunnableLambda(rewrite_question)

    # ---------------------------
    # 4. RETRIEVAL STEP
    # ---------------------------
    def retrieve_docs(inputs):
        question = inputs["rewritten_question"]
        docs = retriever.invoke(question)
        return docs

    retriever_chain = RunnableLambda(retrieve_docs)

    # ---------------------------
    # 5. FINAL ANSWER PROMPT
    # ---------------------------
    system_prompt = """
You are 'Maharaja AI', an expert automated corporate support assistant for Air India.

Answer ONLY using the provided context. Do not make up information.

Context:
{context}

Rules:
- Be highly accurate, brief, and professional.
- If the answer cannot be found in the provided context, state exactly:
  "I am sorry, I cannot find that information in the official Air India policy documents."
- Use clean markdown formatting for tables and schedules where appropriate.
"""

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Final Answer Processing
    def answer_chain(inputs):
        context = format_docs(inputs["docs"])
        
        # Normalize history objects for the QA block template as well
        processed_history = []
        for msg in inputs["chat_history"]:
            if isinstance(msg, tuple):
                role, content = msg
                processed_history.append(HumanMessage(content=content) if role in ["human", "user"] else AIMessage(content=content))
            else:
                processed_history.append(msg)

        chain = qa_prompt | llm

        result = chain.invoke({
            "context": context,
            "input": inputs["input"],
            "chat_history": processed_history
        })

        return {
            "answer": result.content,
            "context": inputs["docs"],
            "context_text": context 
        }

    answer_runnable = RunnableLambda(answer_chain)

    # ---------------------------
    # 6. FULL PIPELINE EXECUTION
    # ---------------------------
    def pipeline(inputs):
        question = question_rewriter.invoke(inputs)

        docs = retriever_chain.invoke({
            "rewritten_question": question
        })

        return answer_runnable.invoke({
            "docs": docs,
            "input": inputs["input"],
            "chat_history": inputs["chat_history"]
        })

    rag_chain = RunnableLambda(pipeline)
    return rag_chain


# ---------------------------
# CLI LOCAL TESTING LOOP
# ---------------------------
if __name__ == "__main__":
    print("🤖 Initializing Maharaja AI Engine...")
    bot = initialize_chatbot()
    chat_history = []

    print("\n🎉 Ready! Type 'exit' to close local testing.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        if not user_input.strip():
            continue

        response = bot.invoke({
            "input": user_input,
            "chat_history": chat_history
        })

        print(f"\nAI: {response['answer']}\n")
        print("-" * 40)

        chat_history.extend([
            ("human", user_input),
            ("ai", response["answer"])
        ])
# import os
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import FAISS
# from langchain.chains import create_history_aware_retriever, create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# load_dotenv()

# def initialize_chatbot():
#     gh_token = os.getenv("GITHUB_TOKEN")
#     if not gh_token:
#         raise ValueError("GITHUB_TOKEN is not set. Please set it in your environment variables.")
    

#     embeddings = HuggingFaceEmbeddings(
#     model_name="BAAI/bge-base-en-v1.5",
#     model_kwargs={"device": "cpu"},
#     encode_kwargs={"normalize_embeddings": True},
# )
#     db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

#     retriever = db.as_retriever(search_kwargs={"k": 4})

#     llm = ChatOpenAI(
#     model="gpt-4o",  # You can also use "gpt-4o-mini" for faster processing
#     api_key=gh_token,
#     base_url="https://models.inference.ai.azure.com",
#     temperature=0.2,
#     )

#     # 3. Memory Context Realignment Prompt

#     contextualize_q_system_prompt = (
#         "Given a chat history and the latest user question "
#         "which might reference context in the chat history, "
#         "formulate a standalone question which can be understood "
#         "without the chat history. Do NOT answer the question, "
#         "just reformulate it if needed and otherwise return it as is."
#     )

#     contextualize_q_prompt = ChatPromptTemplate.from_messages([
#         ("system", contextualize_q_system_prompt),
#         MessagesPlaceholder("chat_history"),
#         ("human", "{input}"),
#     ])

#     history_aware_retriever = create_history_aware_retriever(
#         llm, retriever, contextualize_q_prompt
#     )


#     # 4. Main System Prompt (Persona & Constraints)
#     system_prompt = (
#         "You are 'Maharaja AI', an expert automated corporate support assistant for Air India.\n"
#         "Your job is to answer queries regarding booking policies, GDS violations, and fees "
#         "using ONLY the provided context below. Do not make up facts.\n\n"
#         "Context:\n"
#         "{context}\n\n"
#         "Guidelines:\n"
#         "- If the answer contains a table, display it clearly using Markdown formatting.\n"
#         "- If you do not know the answer or if it's not in the context, say: "
#         "'I am sorry, I cannot find that information in the official Air India policy documents.'\n"
#         "- Be professional, direct, and helpful."
#     )

#     qa_prompt = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         MessagesPlaceholder("chat_history"),
#         ("human", "{input}"),
#     ])


#     # 5. Assemble the complete RAG Chain
#     question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
#     rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
#     return rag_chain


# # Simple Terminal Loop for testing before building the UI
# if __name__ == "__main__":
#     print("🤖 Initializing Maharaja AI... Please wait.")
#     bot = initialize_chatbot()
#     chat_history = []

#     print("\n🎉 Maharaja AI RAG Engine is ready! Type 'exit' to quit.\n")
    
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == 'exit':
#             break
            
#         if not user_input.strip():
#             continue

#         response = bot.invoke({"input": user_input, "chat_history": chat_history})
        
#         print(f"\nAI: {response['answer']}\n")
#         print("-" * 40)
        
#         # Keep track of history
#         chat_history.extend([
#             ("human", user_input),
#             ("ai", response["answer"])
#         ])







import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

load_dotenv()


def initialize_chatbot():
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        raise ValueError("GITHUB_TOKEN is not set in environment variables")

    # ---------------------------
    # 1. Embeddings + Vector DB
    # ---------------------------
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    db = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = db.as_retriever(search_kwargs={"k": 4})

    # ---------------------------
    # 2. LLM
    # ---------------------------
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=gh_token,
        base_url="https://models.inference.ai.azure.com",
        temperature=0.2,
    )

    # ---------------------------
    # 3. QUESTION REWRITER (replacement for history-aware retriever)
    # ---------------------------
    def rewrite_question(inputs):
        question = inputs["input"]
        chat_history = inputs["chat_history"]

        messages = [
            ("system",
             "Rewrite the user question into a standalone question "
             "using chat history if needed. Do NOT answer."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]

        prompt = ChatPromptTemplate.from_messages(messages)

        chain = prompt | llm

        result = chain.invoke({
            "input": question,
            "chat_history": chat_history
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

Answer ONLY using the provided context.

Context:
{context}

Rules:
- Be accurate and professional
- If answer is not in context, say:
  "I am sorry, I cannot find that information in the official Air India policy documents."
- Use markdown for tables if needed.
"""

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    # combine docs into text
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # final answer chain
    def answer_chain(inputs):
        context = format_docs(inputs["docs"])

        chain = qa_prompt | llm

        result = chain.invoke({
            "context": context,
            "input": inputs["input"],
            "chat_history": inputs["chat_history"]
        })

        return {"answer": result.content}

    answer_runnable = RunnableLambda(answer_chain)

    # ---------------------------
    # 6. FULL PIPELINE (LCEL STYLE)
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
# CLI TEST LOOP
# ---------------------------
if __name__ == "__main__":
    print("🤖 Initializing Maharaja AI (LangChain 1.3.11)...")
    bot = initialize_chatbot()
    chat_history = []

    print("\n🎉 Ready! Type 'exit' to quit.\n")

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

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory
from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
)

from chatbot_engine import initialize_chatbot

# Load environment variables
load_dotenv()


def run_ragas_evaluation():
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        raise ValueError("GITHUB_TOKEN not found.")

    print("🤖 Initializing Maharaja AI Engine for testing...")
    bot_chain = initialize_chatbot()

    test_queries = [
        "Does Air India operate flights from Delhi to Jammu?",
        "How many daily flights operate between Delhi and Gaya effective October 25, 2026, and what are their flight numbers?",
        "What is the name change fee for Point-of-Sale locations in the UK?"
    ]

    questions = []
    answers = []
    contexts = []

    print("\n🏃 Running test queries through the RAG system...")
    for query in test_queries:
        print(f"👉 Testing Query: '{query}'")
        response = bot_chain.invoke({
            "input": query,
            "chat_history": []
        })
        print(response)
        questions.append(query)
        answers.append(response["answer"])

        # Get retrieved documents from the chatbot response
        docs = (
            response.get("context")
            or response.get("source_documents")
            or response.get("documents")
            or response.get("retrieved_docs")
            or []
        )

        # Convert Document objects to strings
        retrieved_texts = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]

        # IMPORTANT: Append contexts for every query
        contexts.append(retrieved_texts)

    # Debug
    print("\nCollected Samples")
    print("-----------------")
    print("Questions :", len(questions))
    print("Answers   :", len(answers))
    print("Contexts  :", len(contexts))

    # -------------------------------------------------------------
    # Configure the evaluator LLM/embeddings via GitHub Models
    # (GitHub Models is OpenAI-compatible but needs its own base_url
    # and "openai/" model prefixes, so we build a dedicated client
    # rather than relying on OPENAI_API_KEY pointing at api.openai.com)
    # -------------------------------------------------------------
    github_models_client = AsyncOpenAI(
        api_key=gh_token,
        base_url="https://models.github.ai/inference",
    )

    evaluator_llm = llm_factory(
        "openai/gpt-4o-mini",
        client=github_models_client,
    )
    evaluator_embeddings = embedding_factory(
        "openai",
        model="openai/text-embedding-3-small",
        client=github_models_client,
    )

    # New collections-based metrics require llm (and embeddings) passed in directly
    faithfulness_metric = Faithfulness(llm=evaluator_llm)
    answer_relevancy_metric = AnswerRelevancy(
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    # -------------------------------------------------------------
    # Collections-based metrics are NOT compatible with ragas.evaluate()
    # (that function only accepts the legacy Metric base class).
    # Instead, score each sample directly with .ascore() and average.
    # -------------------------------------------------------------
    async def score_all():
        faithfulness_scores = []
        answer_relevancy_scores = []

        for q, a, ctx in zip(questions, answers, contexts):
            f_result = await faithfulness_metric.ascore(
                user_input=q,
                response=a,
                retrieved_contexts=ctx,
            )
            faithfulness_scores.append(f_result.value)

            ar_result = await answer_relevancy_metric.ascore(
                user_input=q,
                response=a,
            )
            answer_relevancy_scores.append(ar_result.value)

        return faithfulness_scores, answer_relevancy_scores

    print("\n🧮 Submitting data to RAGAS Engine for scoring...")
    faithfulness_scores, answer_relevancy_scores = asyncio.run(score_all())

    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
    avg_answer_relevancy = sum(answer_relevancy_scores) / len(answer_relevancy_scores)

    print("\n📊 ===========================================")
    print("      MAHARAJA AI PERFORMANCE REPORT CARD     ")
    print("=============================================")
    print(f"✨ Faithfulness Score:     {avg_faithfulness:.2f}")
    print(f"✨ Answer Relevancy Score: {avg_answer_relevancy:.2f}")
    print("=============================================")


if __name__ == "__main__":
    run_ragas_evaluation()
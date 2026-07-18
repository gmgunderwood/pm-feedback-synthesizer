import os
from dotenv import load_dotenv
from pinecone import Pinecone, SearchQuery, SearchRerank, RerankModel

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("pm-feedback-test")

test_queries = [
    "Is dark mode available?",
    "How accurate is the GPS for tracking shots?",
    "Is the premium version worth paying for?",
]

for query in test_queries:
    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print('='*70)

    for namespace in ["chunk-test-small", "chunk-test-large"]:
        print(f"\n--- {namespace} ---")

        # Without reranking: top 3 straight from vector similarity
        plain = index.search_records(
            namespace=namespace,
            query=SearchQuery(inputs={"text": query}, top_k=3),
            fields=["chunk_text", "app"],
        )
        print("  WITHOUT reranking:")
        for hit in plain.result.hits:
            print(f"    [{hit['_score']:.3f}] ({hit['fields']['app']}) {hit['fields']['chunk_text'][:100]}...")

        # With reranking: retrieve a wider candidate pool (top 10), rerank down to top 3
        reranked = index.search_records(
            namespace=namespace,
            query=SearchQuery(inputs={"text": query}, top_k=10),
            rerank=SearchRerank(
                model=RerankModel.Bge_Reranker_V2_M3,
                rank_fields=["chunk_text"],
                top_n=3,
            ),
            fields=["chunk_text", "app"],
        )
        print("  WITH reranking:")
        for hit in reranked.result.hits:
            print(f"    [{hit['_score']:.3f}] ({hit['fields']['app']}) {hit['fields']['chunk_text'][:100]}...")
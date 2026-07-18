import os
from dotenv import load_dotenv
from pinecone import Pinecone

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
        results = index.search_records(
            namespace=namespace,
            query={"inputs": {"text": query}, "top_k": 3},
            fields=["chunk_text", "app"],
        )
        print(f"\n--- {namespace} ---")
        for hit in results.result.hits:
            score = hit["_score"]
            text = hit["fields"]["chunk_text"]
            app = hit["fields"]["app"]
            print(f"[{score:.3f}] ({app}) {text[:150]}...")
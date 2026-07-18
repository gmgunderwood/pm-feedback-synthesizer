import os
from dotenv import load_dotenv
from pinecone import Pinecone
import pandas as pd
from chunk_utils import chunk_text

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("pm-feedback-test")

df = pd.read_csv("googleplaystore_reviews_clean.csv")
df["word_count"] = df["Translated_Review"].str.split().str.len()
test_docs = df.nlargest(5, "word_count")[["App", "Translated_Review"]]

strategies = {
    "chunk-test-small": {"chunk_size": 50, "overlap": 10},
    "chunk-test-large": {"chunk_size": 150, "overlap": 20},
}

for namespace, params in strategies.items():
    records = []
    for doc_id, row in test_docs.iterrows():
        chunks = chunk_text(row["Translated_Review"], **params)
        for i, chunk in enumerate(chunks):
            records.append({
                "_id": f"{doc_id}-{i}",
                "chunk_text": chunk,
                "app": row["App"],
            })
    index.upsert_records(namespace=namespace, records=records)
    print(f"{namespace}: {len(records)} chunks ingested from {len(test_docs)} documents")
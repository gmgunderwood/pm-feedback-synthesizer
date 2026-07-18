import os
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd

load_dotenv()

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
)

cur = conn.cursor()
cur.execute("USE DATABASE PROJECT_A")
cur.execute("USE SCHEMA PUBLIC")

# Separate test table, doesn't touch the real APP_REVIEWS table
cur.execute("""
    CREATE OR REPLACE TABLE APP_REVIEWS_SLICE_TEST (
        APP STRING,
        TRANSLATED_REVIEW STRING,
        SENTIMENT STRING,
        SENTIMENT_POLARITY FLOAT,
        SENTIMENT_SUBJECTIVITY FLOAT
    )
""")

df = pd.read_csv("googleplaystore_reviews_clean.csv")
slice_df = df.head(10)
print(f"Local slice row count: {len(slice_df)}")

rows = [
    (r["App"], r["Translated_Review"], r["Sentiment"], r["Sentiment_Polarity"], r["Sentiment_Subjectivity"])
    for _, r in slice_df.iterrows()
]

insert_sql = """
    INSERT INTO APP_REVIEWS_SLICE_TEST
    (APP, TRANSLATED_REVIEW, SENTIMENT, SENTIMENT_POLARITY, SENTIMENT_SUBJECTIVITY)
    VALUES (%s, %s, %s, %s, %s)
"""
cur.executemany(insert_sql, rows)
print(f"Rows inserted via executemany: {cur.rowcount}")

cur.execute("SELECT COUNT(*) FROM APP_REVIEWS_SLICE_TEST")
snowflake_count = cur.fetchone()[0]
print(f"Snowflake table row count: {snowflake_count}")
print(f"Match: {snowflake_count == len(slice_df)}")

cur.close()
conn.close()
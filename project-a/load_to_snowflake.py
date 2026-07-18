"""
load_to_snowflake.py

Project A: loads a cleaned, Snowflake-ready CSV into Snowflake.

This is the tested logic from the Week 5 Snowflake session, refactored
into an importable function so clean_dataset.py can call it directly as
part of a single reproducible run, without duplicating connection or DDL
logic in two places.

Standalone usage (unchanged from before):
    python load_to_snowflake.py

Called from clean_dataset.py:
    from load_to_snowflake import load_to_snowflake
    load_to_snowflake(df, table="APP_REVIEWS")

Requires a .env file (or exported environment variables) with:
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE

Database and schema are not configurable via environment variable on
purpose -- this script is self-provisioning: it creates PROJECT_A.PUBLIC
and the target table if they don't already exist, so a fresh Snowflake
trial can be loaded from nothing with one command.
"""

import os

import pandas as pd
from dotenv import load_dotenv

REQUIRED_ENV_VARS = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_WAREHOUSE",
]

DEFAULT_TABLE = "APP_REVIEWS"
DEFAULT_CLEAN_CSV = "googleplaystore_reviews_clean.csv"


def load_to_snowflake(df: pd.DataFrame, table: str = DEFAULT_TABLE) -> None:
    """
    Load df into Snowflake, self-provisioning the database/schema/table
    along the way, then verify the loaded row count matches the local
    DataFrame exactly.

    Recreates the target table on every call (CREATE OR REPLACE) rather
    than appending, so a run of this function is always a full, reproducible
    refresh rather than something that depends on what was loaded last time.

    Table name is an f-string parameter here, not user-supplied web input --
    it's controlled by the same person running the script from the CLI, so
    this is safe in that context but would need parameterized identifiers
    if this logic were ever exposed beyond a local script.
    """
    load_dotenv()

    missing_vars = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing Snowflake environment variable(s): {', '.join(missing_vars)}. "
            "Set these in a .env file or export them before running with --load."
        )

    import snowflake.connector
    from snowflake.connector.pandas_tools import write_pandas

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    )

    try:
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS PROJECT_A")
        cur.execute("USE DATABASE PROJECT_A")
        cur.execute("CREATE SCHEMA IF NOT EXISTS PUBLIC")
        cur.execute("USE SCHEMA PUBLIC")

        cur.execute(f"""
            CREATE OR REPLACE TABLE {table} (
                APP STRING,
                TRANSLATED_REVIEW STRING,
                SENTIMENT STRING,
                SENTIMENT_POLARITY FLOAT,
                SENTIMENT_SUBJECTIVITY FLOAT
            )
        """)

        # Defensive: uppercase columns even if the caller already did this
        # upstream (clean_dataset.py's rename_for_snowflake step does).
        # A no-op when columns are already uppercase, a safety net when not.
        upload_df = df.copy()
        upload_df.columns = [c.upper() for c in upload_df.columns]

        success, num_chunks, num_rows, _ = write_pandas(conn, upload_df, table)
        print(f"Upload success: {success}, rows loaded: {num_rows:,}")

        cur.execute(f"SELECT COUNT(*) FROM {table}")
        snowflake_count = cur.fetchone()[0]
        print(f"Snowflake table row count: {snowflake_count:,}")
        print(f"Match: {snowflake_count == len(upload_df)}")

        cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    # Standalone behavior, unchanged from before the refactor: read the
    # clean CSV from disk and load it, rather than receiving a DataFrame
    # from clean_dataset.py in the same process.
    df = pd.read_csv(DEFAULT_CLEAN_CSV)
    load_to_snowflake(df, DEFAULT_TABLE)
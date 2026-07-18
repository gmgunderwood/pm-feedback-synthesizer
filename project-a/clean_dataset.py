"""
clean_dataset.py

Project A: end-to-end pipeline for the Google Play Store User Reviews
dataset, from raw CSV to a Snowflake-ready clean CSV, with an optional
final step that loads the result directly into Snowflake.

Pipeline stages, always run in this order:
    1. Load the raw CSV.
    2. Clean it (missing reviews, whitespace, duplicates, sentiment
       labels, numeric score ranges) -- every step here was independently
       verified against the real 64,295-row dataset in Week 4.
    3. Rename columns to their final Snowflake identifiers.
    4. Write the clean, Snowflake-ready CSV to disk.
    5. Optionally: load that same data straight into Snowflake, by calling
       the tested load_to_snowflake() function from load_to_snowflake.py,
       if --load is passed and Snowflake credentials are present.

Usage:
    # Clean only -- always safe, no network calls, no credentials needed.
    python clean_dataset.py

    # Clean, then also load the result into Snowflake.
    python clean_dataset.py --load

    # Override paths, target table, or warehouse/schema as needed.
    python clean_dataset.py --input path/to/raw.csv --output path/to/clean.csv --load --table APP_REVIEWS

Run standalone and reproducibly: no notebook state, no hidden steps, no
step that silently depends on something done outside this file. Every
cleaning decision is a named, commented function so the whole pipeline
can be explained in an interview without re-deriving it from scratch.
"""

import argparse
from pathlib import Path

import pandas as pd

# Default paths assume this script lives in the Project A folder alongside
# the raw and cleaned CSVs.
DEFAULT_INPUT = "googleplaystore_user_reviews.csv"
DEFAULT_OUTPUT = "googleplaystore_reviews_clean.csv"
DEFAULT_TABLE = "APP_REVIEWS"

TEXT_COLUMN = "Translated_Review"
SENTIMENT_COLUMN = "Sentiment"
POLARITY_COLUMN = "Sentiment_Polarity"
SUBJECTIVITY_COLUMN = "Sentiment_Subjectivity"

VALID_SENTIMENTS = {"Positive", "Negative", "Neutral"}
POLARITY_RANGE = (-1.0, 1.0)
SUBJECTIVITY_RANGE = (0.0, 1.0)

# Snowflake stores unquoted identifiers as uppercase. Making that mapping
# explicit here -- rather than relying on Snowflake to auto-uppercase
# whatever pandas hands it -- is what actually makes the output
# "Snowflake-ready" rather than merely "Snowflake-compatible by luck."
SNOWFLAKE_COLUMN_MAP = {
    "App": "APP",
    "Translated_Review": "TRANSLATED_REVIEW",
    "Sentiment": "SENTIMENT",
    "Sentiment_Polarity": "SENTIMENT_POLARITY",
    "Sentiment_Subjectivity": "SENTIMENT_SUBJECTIVITY",
}


def load_raw(path: str) -> pd.DataFrame:
    """Load the raw CSV and report the starting row count."""
    df = pd.read_csv(path)
    print(f"Loaded {len(df):,} raw rows from {path}")
    return df


def drop_missing_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows with no review text.

    This dataset has two distinct flavors of "missing": genuine NaN (from
    pandas reading an empty cell) and the literal string "nan" (a known
    quirk of this specific CSV export, not a pandas artifact). Both have to
    be handled explicitly, since .dropna() alone only catches the first.
    This step accounts for the large majority of dropped rows (41.8% on
    the real dataset).
    """
    before = len(df)
    df = df.dropna(subset=[TEXT_COLUMN])
    df = df[df[TEXT_COLUMN].astype(str).str.strip().str.lower() != "nan"]
    df = df[df[TEXT_COLUMN].astype(str).str.strip() != ""]
    dropped = before - len(df)
    pct = (dropped / before * 100) if before else 0
    print(f"Dropped {dropped:,} rows with missing/blank review text ({pct:.1f}%)")
    return df


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip leading/trailing whitespace from all string columns.

    Runs before deduplication on purpose: two rows that differ only by a
    trailing space are the same review, and drop_duplicate_reviews() does
    an exact-match comparison, so it would miss them if this ran after.
    """
    str_cols = [c for c in df.columns if pd.api.types.is_string_dtype(df[c])]
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    return df


def drop_duplicate_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop exact duplicate rows.

    Duplicates here are full-row duplicates (same app, same review text,
    same sentiment fields) rather than just duplicate review text, since
    the same review string could legitimately appear under two different
    apps. 7,735 duplicates dropped on the real dataset.
    """
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    print(f"Dropped {dropped:,} exact duplicate rows")
    return df


def clean_sentiment_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows with a recognized sentiment label.

    Anything outside {"Positive", "Negative", "Neutral"} -- an unexpected
    category, a typo, a null -- is dropped rather than remapped, since
    silently reassigning an unrecognized label to the nearest valid one
    would be inventing a sentiment the source data never actually gave us.
    """
    before = len(df)
    df = df[df[SENTIMENT_COLUMN].isin(VALID_SENTIMENTS)]
    dropped = before - len(df)
    print(f"Dropped {dropped:,} rows with missing/invalid sentiment label")
    return df


def clean_numeric_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce polarity/subjectivity to numeric and drop rows outside their
    valid ranges.

    Sentiment_Polarity is expected in [-1, 1] and Sentiment_Subjectivity in
    [0, 1]. Values outside those ranges (or non-numeric after coercion)
    indicate a corrupted row rather than a real score, so they're dropped
    rather than clipped, to avoid quietly inventing data.
    """
    before = len(df)

    df[POLARITY_COLUMN] = pd.to_numeric(df[POLARITY_COLUMN], errors="coerce")
    df[SUBJECTIVITY_COLUMN] = pd.to_numeric(df[SUBJECTIVITY_COLUMN], errors="coerce")

    df = df.dropna(subset=[POLARITY_COLUMN, SUBJECTIVITY_COLUMN])

    lo_p, hi_p = POLARITY_RANGE
    lo_s, hi_s = SUBJECTIVITY_RANGE
    df = df[df[POLARITY_COLUMN].between(lo_p, hi_p)]
    df = df[df[SUBJECTIVITY_COLUMN].between(lo_s, hi_s)]

    dropped = before - len(df)
    print(f"Dropped {dropped:,} rows with invalid/out-of-range polarity or subjectivity")
    return df


def reset_and_finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Reset the index after all filtering so the clean CSV is tidy."""
    return df.reset_index(drop=True)


def rename_for_snowflake(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to their final Snowflake identifiers.

    This is what actually makes the output "Snowflake-ready" rather than
    just clean: the mapping is explicit and versioned in this file, so the
    pipeline doesn't depend on Snowflake's auto-uppercasing behavior to
    happen to line up with what VW_APP_SENTIMENT_SUMMARY and the other
    views expect.
    """
    missing = set(SNOWFLAKE_COLUMN_MAP) - set(df.columns)
    if missing:
        raise KeyError(
            f"Expected column(s) {sorted(missing)} not found before Snowflake "
            "rename -- the raw schema may have changed."
        )
    return df.rename(columns=SNOWFLAKE_COLUMN_MAP)


def clean(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Run the full raw-to-Snowflake-ready pipeline (steps 1-4) and write the
    result to output_path. Does not load to Snowflake -- see main() for
    the optional --load step.
    """
    df = load_raw(input_path)
    raw_count = len(df)

    df = drop_missing_reviews(df)
    df = strip_whitespace(df)
    df = drop_duplicate_reviews(df)
    df = clean_sentiment_labels(df)
    df = clean_numeric_scores(df)
    df = reset_and_finalize(df)
    df = rename_for_snowflake(df)

    df.to_csv(output_path, index=False)

    final_count = len(df)
    total_dropped = raw_count - final_count
    total_pct = (total_dropped / raw_count * 100) if raw_count else 0

    print("-" * 60)
    print(f"Raw rows:      {raw_count:,}")
    print(f"Clean rows:    {final_count:,}")
    print(f"Total dropped: {total_dropped:,} ({total_pct:.1f}%)")
    print(f"Clean, Snowflake-ready CSV written to: {output_path}")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean the Project A raw reviews CSV and optionally load it into Snowflake."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the raw CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write the clean CSV")
    parser.add_argument(
        "--load",
        action="store_true",
        help="After cleaning, also load the result into Snowflake (requires env vars).",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help=f"Target Snowflake table name when --load is passed (default: {DEFAULT_TABLE})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not Path(args.input).exists():
        raise FileNotFoundError(
            f"Could not find raw CSV at '{args.input}'. "
            "Run this script from the Project A folder, or pass --input explicitly."
        )

    df = clean(args.input, args.output)

    if args.load:
        print("-" * 60)
        # Imported here, not at module level, so that running this script
        # without --load never requires snowflake-connector-python or
        # python-dotenv to be installed.
        from load_to_snowflake import load_to_snowflake

        load_to_snowflake(df, table=args.table)


if __name__ == "__main__":
    main()
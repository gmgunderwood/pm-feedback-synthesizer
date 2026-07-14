"""
clean_dataset.py

Project A: cleaning pipeline for the Google Play Store User Reviews dataset.

Takes the raw CSV (App, Translated_Review, Sentiment, Sentiment_Polarity,
Sentiment_Subjectivity), applies every cleaning step identified during the
pandas study sessions, and writes a clean CSV alongside a short summary of
what was dropped and why.

Usage:
    python clean_dataset.py
    python clean_dataset.py --input path/to/raw.csv --output path/to/clean.csv

Run standalone and reproducibly: no notebook state, no hidden steps. Every
cleaning decision below is a named, commented step so it can be explained
in an interview without re-deriving it from scratch.
"""

import argparse
from pathlib import Path

import pandas as pd

# Default paths assume this script lives in the Project A folder alongside
# the raw and cleaned CSVs.
DEFAULT_INPUT = "googleplaystore_user_reviews.csv"
DEFAULT_OUTPUT = "googleplaystore_reviews_clean.csv"

TEXT_COLUMN = "Translated_Review"
SENTIMENT_COLUMN = "Sentiment"
POLARITY_COLUMN = "Sentiment_Polarity"
SUBJECTIVITY_COLUMN = "Sentiment_Subjectivity"

VALID_SENTIMENTS = {"Positive", "Negative", "Neutral"}
POLARITY_RANGE = (-1.0, 1.0)
SUBJECTIVITY_RANGE = (0.0, 1.0)


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
    This step accounts for the large majority of dropped rows.
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
    """Strip leading/trailing whitespace from all string columns."""
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
    apps.
    """
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    print(f"Dropped {dropped:,} exact duplicate rows")
    return df


def clean_sentiment_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with a recognized sentiment label."""
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


def clean(input_path: str, output_path: str) -> pd.DataFrame:
    """Run the full cleaning pipeline and write the result to output_path."""
    raw_count = None

    df = load_raw(input_path)
    raw_count = len(df)

    df = drop_missing_reviews(df)
    df = strip_whitespace(df)
    df = drop_duplicate_reviews(df)
    df = clean_sentiment_labels(df)
    df = clean_numeric_scores(df)
    df = reset_and_finalize(df)

    df.to_csv(output_path, index=False)

    final_count = len(df)
    total_dropped = raw_count - final_count
    total_pct = (total_dropped / raw_count * 100) if raw_count else 0

    print("-" * 60)
    print(f"Raw rows:    {raw_count:,}")
    print(f"Clean rows:  {final_count:,}")
    print(f"Total dropped: {total_dropped:,} ({total_pct:.1f}%)")
    print(f"Clean CSV written to: {output_path}")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean the Project A raw reviews CSV.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the raw CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write the clean CSV")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not Path(args.input).exists():
        raise FileNotFoundError(
            f"Could not find raw CSV at '{args.input}'. "
            "Run this script from the Project A folder, or pass --input explicitly."
        )

    clean(args.input, args.output)

import pandas as pd

INPUT_FILE = "googleplaystore_user_reviews.csv"
OUTPUT_FILE = "googleplaystore_reviews_clean.csv"

print("Loading:", INPUT_FILE)
df = pd.read_csv(INPUT_FILE)
print("Raw shape:", df.shape)

df = df.dropna(subset=["Translated_Review"])
print("After dropping null reviews:", df.shape)

df["Translated_Review"] = df["Translated_Review"].str.strip()
df["App"] = df["App"].str.strip()
df["Sentiment"] = df["Sentiment"].str.strip()

valid = ["Positive", "Negative", "Neutral"]
df = df[df["Sentiment"].isin(valid)]
print("After filtering valid sentiments:", df.shape)

df["word_count"] = df["Translated_Review"].str.split().str.len()

nulls = df.isnull().sum().sum()
print("Remaining nulls:", nulls)

print(df["Sentiment"].value_counts())
print(df.groupby("Sentiment")["Sentiment_Polarity"].mean().round(3))
print(df["word_count"].describe().round(1))

df.to_csv(OUTPUT_FILE, index=False)
print("Saved:", OUTPUT_FILE)
print("Final shape:", df.shape)
print("Columns:", list(df.columns))
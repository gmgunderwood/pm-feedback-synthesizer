import pandas as pd

df = pd.read_csv('reviews.csv')
print('=== 1. SHAPE AND COLUMNS ===')
print('Rows:', len(df), '| Columns:', list(df.columns))

df['date'] = pd.to_datetime(df['date'])
df['review_text'] = df['review_text'].str.strip()
df['word_count'] = df['review_text'].str.split().str.len()
print('\n=== 2. AFTER CLEANING ===')
print(df[['date', 'rating', 'platform', 'word_count']].head())

print('\n=== 3. AGGREGATIONS ===')
print('Avg rating:', round(df['rating'].mean(), 2))
print('Rating counts:')
print(df['rating'].value_counts().sort_index())

print('\n=== 4. GROUPBY: avg rating by platform ===')
print(df.groupby('platform')['rating'].mean().round(2))

print('\n=== 4b. GROUPBY: count and avg by country ===')
print(df.groupby('country').agg(count=('rating','count'), avg=('rating','mean')).round(2))

print('\n=== 5. SORT: lowest rated first ===')
print(df.sort_values('rating')[['rating','platform','country','review_text']].head(4).to_string())

print('\n=== 6. FILTER: 1-star only ===')
print(df[df['rating']==1][['platform','country','review_text']].to_string())

df.to_csv('reviews_clean.csv', index=False)
print('\n=== 7. SAVED reviews_clean.csv ===')
print('Columns:', list(df.columns))

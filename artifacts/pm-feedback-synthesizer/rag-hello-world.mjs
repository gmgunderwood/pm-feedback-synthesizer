import { Pinecone } from '@pinecone-database/pinecone';

console.log('Starting...');
console.log('API key present:', !!process.env.PINECONE_API_KEY);

try {
  const pc = new Pinecone({ apiKey: process.env.PINECONE_API_KEY });
  const indexName = 'pm-feedback-test';
  const index = pc.index(indexName).namespace('test');

  console.log('Upserting records one by one...');
  await index.upsertRecords({ _id: '1', chunk_text: 'The synthesis feature is great but sometimes too verbose' });
  await index.upsertRecords({ _id: '2', chunk_text: 'I wish the app could group similar feedback automatically' });
  await index.upsertRecords({ _id: '3', chunk_text: 'Response time is too slow when processing large feedback sets' });
  await index.upsertRecords({ _id: '4', chunk_text: 'The UI is clean and intuitive, easy to get started' });
  await index.upsertRecords({ _id: '5', chunk_text: 'Would love a way to export the synthesized results to CSV' });
  await index.upsertRecords({ _id: '6', chunk_text: 'Sometimes the summary misses the most critical feedback points' });
  await index.upsertRecords({ _id: '7', chunk_text: 'Great tool for PMs, saves a lot of manual analysis time' });
  console.log('Upserted 7 records.');

  await new Promise(r => setTimeout(r, 5000));

  const query = 'users want better export options';
  console.log('\nQuerying:', query);

  const results = await index.searchRecords({
    query: { inputs: { text: query }, topK: 3 },
    fields: ['chunk_text'],
  });

  console.log('\nTop 3 results:');
  results.result.hits.forEach((hit, i) => {
    console.log(`${i + 1}. [score: ${hit._score.toFixed(3)}] ${hit.fields.chunk_text}`);
  });

} catch (err) {
  console.error('ERROR:', err.message);
  console.error(err);
}
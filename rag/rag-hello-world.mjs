import { Pinecone } from '@pinecone-database/pinecone';
console.log('Starting...');
const pc = new Pinecone({ apiKey: process.env.PINECONE_API_KEY });
const index = pc.index('pm-feedback-test').namespace('test');
console.log('Upserting...');
await index.upsertRecords({ records: [
  { _id: '1', chunk_text: 'synthesis feature sometimes too verbose' },
  { _id: '2', chunk_text: 'group similar feedback automatically' },
  { _id: '3', chunk_text: 'response time too slow for large sets' },
  { _id: '4', chunk_text: 'UI is clean and intuitive' },
  { _id: '5', chunk_text: 'export synthesized results to CSV' },
  { _id: '6', chunk_text: 'summary misses critical feedback points' },
  { _id: '7', chunk_text: 'great tool for PMs saves manual analysis time' }
]});
console.log('Upserted 7 records.');
await new Promise(r => setTimeout(r, 5000));
const results = await index.searchRecords({ query: { inputs: { text: 'export options' }, topK: 3 }, fields: ['chunk_text'] });
console.log('Results:');
results.result.hits.forEach((h, i) => console.log(i+1, h._score.toFixed(3), h.fields.chunk_text));

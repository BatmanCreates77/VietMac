import { MongoClient } from 'mongodb';

const uri = process.env.MONGO_URL;
const dbName = process.env.DB_NAME;

let cachedClient = null;
let cachedDb = null;

if (!uri) {
  throw new Error(
    'Please define the MONGO_URL environment variable inside .env.local'
  );
}

if (!dbName) {
  throw new Error(
    'Please define the DB_NAME environment variable inside .env.local'
  );
}

export async function connectToDatabase() {
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb };
  }

  const client = await MongoClient.connect(uri, {});

  const db = await client.db(dbName);

  cachedClient = client;
  cachedDb = db;

  return { client, db };
}

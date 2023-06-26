import { PineconeClient } from "@pinecone-database/pinecone";

const pinecone = new PineconeClient();
await pinecone.init({
  environment: "northamerica-northeast1-gcp",
  apiKey: process.env.PINECONE_API_KEY,
});

export const findLimitVectorQuery = (query: string, limit: number, namespace: string) => {};
export const findOneVectorQuery = (query: string, namespace: string) => {};


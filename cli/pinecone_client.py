import os
import pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

pinecone.init(api_key=os.environ['PINECONE_API_KEY'], environment="northamerica-northeast1-gcp")
index = pinecone.Index("food")

model = SentenceTransformer('all-MiniLM-L6-v2')

def find_limit_vector_query(query, limit, namespace, providedModel = model):
    matches = index.query(
        vector=providedModel.encode(query).tolist(),
        top_k=limit,
        include_values=True,
        namespace=namespace,
        include_metadata=True
    )['matches']

    return matches

def find_one_vector_query(query, namespace, providedModel = model):
    matches = index.query(
        vector=providedModel.encode(query).tolist(),
        top_k=1,
        include_values=True,
        namespace=namespace,
        include_metadata=True
    )['matches']

    if len(matches) == 0:
        return None

    return matches[0]

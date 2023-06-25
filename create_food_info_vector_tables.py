import pinecone
import sqlite3
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
db = sqlite3.connect('food.db')

pinecone.init(api_key=os.environ['PINECONE_API_KEY'], environment="northamerica-northeast1-gcp")

index = pinecone.Index("food")

"""
data = list (id, embedding)
"""
def upload_chunks(data, namespace):
    for i in range(0, len(data), 1000):
        chunk = data[i:i+1000]
        if len(chunk) > 0:
            index.upsert(chunk, namespace=namespace)

def insert_measurement_embeddings():
    measures = db.execute('select distinct Msre_Desc from weight;').fetchall()
    names = [m[0] for m in measures]

    data = list(zip(names, [m.tolist() for m in model.encode(names)]))
    upload_chunks(data, 'measures')
    

def insert_td_embeddings():
    food = db.execute('select distinct name from td_types;').fetchall()
    food_names = [f[0] for f in food]
    data = list(zip(food_names, [m.tolist() for m in model.encode(food_names)]))

    upload_chunks(data, 'td')

def insert_food_info_embeddings():
    food = db.execute('select distinct NDB_No, Long_Desc from food_info_types;').fetchall()
    food_names = [f[1] for f in food]
    data = list(zip([str(f[0]) for f in food], [m.tolist() for m in model.encode(food_names)]))

    upload_chunks(data, 'info')

#insert_td_embeddings()
#index.delete(deleteAll='true', namespace='info')
#insert_food_info_embeddings()
#insert_measurement_embeddings()

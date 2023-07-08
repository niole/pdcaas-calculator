import sqlite3
from itertools import groupby
import json
from sentence_transformers import SentenceTransformer
import pinecone
from pinecone_client import find_limit_vector_query, find_one_vector_query

model = SentenceTransformer('all-MiniLM-L6-v2')
db = sqlite3.connect('food.db')

index = pinecone.Index("food")

essential_amino_acids = ["Tryptophan","Threonine","Isoleucine","Leucine","Lysine","Methionine","Phenylalanine","Valine","Histidine"]
EAAS_QUERY_STRING = ','.join(["'" + a + "'" for a in essential_amino_acids])

"""
data = list (id, embedding)
"""
def upload_chunks(data, namespace):
    c_size = 500
    for i in range(0, len(data), c_size):
        chunk = data[i:i+c_size]
        if len(chunk) > 0:
            index.upsert(chunk, namespace=namespace)

def encode_str_list(data):
    return [m.tolist() for m in model.encode(data)]

def group_to_dict(group):
    d = {}
    for (k, v) in group:
        d[k] = list(v)

    return d

def insert_measurement_embeddings():
    measures = db.execute('select distinct Msre_Desc from weight;').fetchall()
    names = [m[0] for m in measures]

    data = list(zip(names, [m.tolist() for m in model.encode(names)]))
    upload_chunks(data, 'measures')
    

def insert_td_embeddings():
    # TODO add td_score metadata
    #index.delete(deleteAll='true', namespace='td')
    food = db.execute('select distinct * from td_types;').fetchall()
    food_names = [f[0] for f in food]
    td_scores = [{'td_score': f[1]} for f in food]
    data = list(zip(food_names, [m.tolist() for m in model.encode(food_names)], td_scores))

    upload_chunks(data, 'td')

def insert_food_info_embeddings():
    food = db.execute('select distinct NDB_No, Long_Desc from food_info_types;').fetchall()
    food_names = [f[1] for f in food]
    data = list(zip([str(f[0]) for f in food], [m.tolist() for m in model.encode(food_names)]))

    upload_chunks(data, 'info')

def insert_food_embeddings_with_metadata():
    upsert_map = {}
    grouped_food = {}
    weight_result = {}
    # metadata = { protein_g: number, amino_acids: []"{name: str, per100g: int}", td_score: number, weights: []"{msre_desc: string, gm_weight: int}"}
    food = list(db.execute("select  NDB_No, Nutr_Val, Long_Desc, NutrDesc from food_info_types where NutrDesc in ('Protein',"+EAAS_QUERY_STRING+");").fetchall())
    grouped_food = group_to_dict(groupby(food, lambda x: x[0]))

    ids = ",".join([f"'{f}'" for f in grouped_food.keys()])
    weight_result = group_to_dict(groupby(db.execute("select NDB_No, Msre_Desc, Gm_Wgt from weight where NDB_No in ("+ids+")").fetchall(), lambda x: x[0]))

    for (id, all_protein_data) in grouped_food.items():
        all_protein_data = list(all_protein_data)
        if len(all_protein_data) > 0:
            upsert_map[id] = {}
            upsert_map[id]['weights'] = []
            upsert_map[id]['aas'] = []

            if id in weight_result:
                upsert_map[id]['weights'] = [json.dumps({'Msre_Desc': w[1], 'Gm_Wgt': w[2]}) for w in weight_result[id]]

            d = all_protein_data[0]
            upsert_map[id]['tmp_name'] = d[2]
            td_result = find_one_vector_query(d[2], 'td') # TODO could update this to have metadata for the td score
            if td_result is not None and "td_score" in td_result["metadata"]:
                score_result = td_result["metadata"]["td_score"]
                upsert_map[id]['td_score'] = score_result


        for food_info in all_protein_data:
            (NDB_No, per_100g, food_desc, nutrdesc) = food_info

            if nutrdesc == 'Protein':
                upsert_map[id]['protein_per_100g'] = per_100g
            else:
                upsert_map[id]['aas'].append(json.dumps({
                    'name': nutrdesc,
                    'per100g': per_100g,
                }))


    id_metadata = upsert_map.items()
    embeddings = encode_str_list([idm[1]['tmp_name'] for idm in id_metadata])
    upserts = list(zip([i[0] for i in id_metadata], embeddings, [i[1] for i in id_metadata]))
    upload_chunks(upserts, 'info')

def embed_recipes():
    pass

#insert_td_embeddings()
#index.delete(deleteAll='true', namespace='info')
#insert_food_info_embeddings()
#insert_measurement_embeddings()
#insert_food_embeddings_with_metadata()

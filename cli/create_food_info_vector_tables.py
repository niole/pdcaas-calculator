import sqlite3
import click
from itertools import groupby
import json
from sentence_transformers import SentenceTransformer
import pinecone
from pinecone_client import find_one_vector_query

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

# TODO allow model to be pluggable
def encode_str_list(data, providedModel = model):
    return [m.tolist() for m in providedModel.encode(data)]

def group_to_dict(group):
    d = {}
    for (k, v) in group:
        d[k] = list(v)

    return d

def insert_measurement_embeddings(providedModel = model):
    measures = db.execute('select distinct Msre_Desc from weight;').fetchall()
    names = [m[0] for m in measures]

    data = list(zip(names, [m.tolist() for m in providedModel.encode(names)]))
    upload_chunks(data, 'measures')
    

def insert_td_embeddings(providedModel = model):
    food = db.execute('select distinct * from td_types;').fetchall()
    food_names = [f[0] for f in food]
    td_scores = [{'td_score': f[1]} for f in food]
    data = list(zip(food_names, [m.tolist() for m in providedModel.encode(food_names)], td_scores))

    upload_chunks(data, 'td')

"""
Embeds the Long_Desc of all food_info_types food items and adds the weights, amino acid data, and TD score as metadata

TODO also embeds previously scored recipes as food items, ingredients are the results of recipes and good items
This would mean that we have to store some kind of weight data on the recipe, maybe the weight in grams, bc supposedly I would be able to calculate that, the TD score is the digestible protein/total protein, amino acid data could be calculated

when a recipe is successfully scored, it also goes into the "info" namespace,
then for recipes that aren't successfully scored, we could run the script again. Should store the recipes that are "WIP" in sqlite.

a recipe is successfullly scored when all ingredients were completely findable in the "info" namespace and we scored the recipe.

successfully scored recipes are embedded in the "info" namespace as food items

unsuccessfullly scored recipes live in a collection in sqlite called "recipes"....

in order to make sure that we can score things properly, we need to fine-tune the sentence transformer to match ingredients to food in food_info_types

1. fine tune sentence transformer. I think we want to choose a data representation that indicates that something does and does not match, maybe see what the sentence transformer currently scores the thing as and if it's too high and it's wrong, give it a low score. then manually go and find the right match
2. re-embed all food_info_types entries into the info namespace with the new model
3. ingest all recipes into sqlite. The recipe data collections will have a notion of successful scoring
4. score the recipes, successfully scored recipes will be embedded in the "info" namespace, unsuccessfullly scored recipes will only exist in sqlite
5. run 2 rounds of scoring for the recipes in sqlite, by then you will have the recipes that were immediately scorable and the recipes that are not possible to complete given the state of the food db, the current recipes, the sentence transformer
6. evaluate the unsuccessfullly scored recipes
"""
def insert_food_embeddings_with_metadata(providedModel = model):
    food_item_transformer = providedModel

    # NDB_No -> { weights, aas, td_score, protein_per_100g }
    upsert_map = {}
    grouped_food = {}
    weight_result = {}

    # metadata = { protein_g: number, amino_acids: []{name: str, per100g: int}, td_score: number, weights: []{Msre_Desc: string, Gm_Weight: int}}
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

            td_result = find_one_vector_query(d[2], 'td')
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


    # upsert everything into info namespace
    id_metadata = upsert_map.items()
    embeddings = encode_str_list([idm[1]['tmp_name'] for idm in id_metadata], providedModel = food_item_transformer)
    upserts = list(zip([i[0] for i in id_metadata], embeddings, [i[1] for i in id_metadata]))
    upload_chunks(upserts, 'info')

def insert_recipes(recipe_paths, providedModel = model):
    def get_metadata(r):
        breakdown = r["nutrient_breakdown"]["protein_breakdown"]
        return {
            "percent_complete_digestible_protein": breakdown["percent_complete_digestible_protein"],
            "total_complete_digestible_protein_g": breakdown["total_complete_digestible_protein_g"],
            "total_protein_g": breakdown["total_protein_g"],
        }

    for path in recipe_paths:
        with open(path, 'r') as file:
            recipes = json.loads(file.read())
            titles = [r['title'] for r in recipes if r is not None]

            metadata = [get_metadata(r) for r in recipes]
            upserts = list(zip(titles, encode_str_list(titles, providedModel), metadata))
            upload_chunks(upserts, 'recipes')

"""
returns the basic model or the one located on disk
"""
def get_model(model_path):
    if model_path is not None:
        return SentenceTransformer(model_path)
    else:
        return model


@click.command()
@click.option('--model_path', type=str, required=False)
@click.option('--embed_weights', is_flag=True, default=False)
@click.option('--embed_td', is_flag=True, default=False)
@click.option('--embed_food_items', is_flag=True, default=False)
@click.option('--embed_recipes', is_flag=True, default=False)
@click.option('--recipe_paths', multiple=True, default=[])
def main(model_path, embed_weights, embed_td, embed_food_items, embed_recipes, recipe_paths):
    resolved_model = get_model(model_path)

    if embed_recipes:
        insert_recipes(recipe_paths, providedModel=resolved_model)

    if embed_weights:
        insert_measurement_embeddings(providedModel=resolved_model)

    if embed_td:
        insert_td_embeddings(providedModel=resolved_model)

    if embed_food_items:
        insert_food_embeddings_with_metadata(providedModel=resolved_model)


if __name__ == "__main__":
    main()

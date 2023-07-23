import os
import traceback
import re
import click
from functools import partial
import json
import logging
from sentence_transformers import SentenceTransformer
import pinecone
from multiprocessing import Pool
import multiprocessing
from pinecone_client import find_limit_vector_query, find_one_vector_query
from get_file_name import get_file_name
from get_gram_weight import get_gram_weight
from models.amino_acid import AminoAcid
from models.ingredient import Ingredient
from models.recipe import Recipe
from essential_amino_acid_utils import EAA_PROPORTIONS
from dotenv import load_dotenv
load_dotenv()

logger = multiprocessing.get_logger()
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

model = SentenceTransformer('./transformers/food_item_transformer')

BAREFOOT_CONTESSA_JSON = 'open_ai/data/barefootcontessa_array.json'
OH_SHE_GLOWS_JSON = 'open_ai/data/ohsheglows_array.json'

def get_matching_food_items(query):
    ms = list(find_limit_vector_query(query, 20, 'info', model))

    return [m for m in ms if m['score'] >= 0.7]

"""
This calculates the proportion of protein that is digestible complete protein.
This is calculated for 1 recipe.

For each ingredient in a recipe, this finds the food entry that best matches it, computes the weight in grams, and uses the Total Digestibility score
to compute the amount of protein that will provide nutrition.

Information such as amino acid data, and conversion information for the  food entry are stored as metadata in the vector database

computing gram weight: if there is a weight entry in cup, tsp, teaspoon, tbsp, tablespoon, we can probably work with that
find closest match for ingredient in food_info or td_types: put all food names into a collection in a vector db and all td_types in their own collection
and do a search
"""
def cli(recipe):
    logger.warning(f"Computing protein data for recipe{recipe['title']}")

    ingredients = []
    for ing in recipe['ingredients_w_units']:
        logger.warning(f"Getting data for ingredient {ing}")

        food_query = ing['name']
        measure_units_query = ing['units']
        measure_amount_query = float(ing['total'])


        # each food item has it's name, id, per 100g stats for protein and amino acids, and the td score
        food_items = get_matching_food_items(food_query)

        if len(food_items) == 0:
            logger.warning(f"Couldn't find a matching food item for query {food_query}")
            continue

        for food_item in food_items:
            food_match_id = food_item['id']
            metadata = food_item['metadata']
            food_match_name = metadata['tmp_name']
            print(f"{food_match_name} metadata {metadata}")

            logger.debug(f"Found food item match for request {food_query}: {food_match_name}, id {food_match_id}")

            aas = [json.loads(a) for a in metadata['aas']]
            weights = [json.loads(w) for w in metadata['weights']]

            td_score = None
            if 'td_score' in metadata:
                td_score = metadata['td_score']

            ingredient = None
            gram_weight = None

            for weight in weights:
                gram_weight = get_gram_weight(food_query, measure_units_query, measure_amount_query, weight['Msre_Desc'], weight['Gm_Wgt'])
                if gram_weight is not None:
                    break

            if gram_weight is None:
                logger.warning(f"Insufficient weight data. Can't convert {food_query} measurement to grams, units: {measure_amount_query}, amount: {measure_units_query}.")
                continue

            # calculate total protein grams in queried amount of food
            protein_per_g = metadata['protein_per_100g']/100
            total_protein_ing_g = protein_per_g*gram_weight
            print(total_protein_ing_g)

            ingredient = Ingredient(
                food_query,
                food_match_name,
                food_match_id,
                td_score,
                total_protein_ing_g,
                measure_amount_query,
                measure_units_query,
                [AminoAcid(f['name'], total_protein_ing_g*f['per100g']/100) for f in aas]
            )

            ingredients.append(ingredient)
            break

    scored_recipe = Recipe(recipe["id"], recipe["title"], ingredients, recipe["ingredients"])

    if len(ingredients) < len(recipe['ingredients_w_units']) or not scored_recipe.is_scored():
        logger.warning(f"Failed to score all ingredients in recipe {recipe['title']}")

        # TODO update database entry with scoring data from scored_recipe

    return scored_recipe

"""
Computes the protein breakdown for a recipe by finding a nutrient vector match
"""
def add_protein_data(recipe, outpath):
    try:
        scored_recipe = cli(recipe)

        with open(outpath, 'a') as outfile:
            outfile.write(json.dumps(scored_recipe.to_json()))

    except Exception as e:
        traceback.print_exc()
        logger.error(f'Something went wrong when getting protein data for {recipe["title"]}: {e}')

@click.command()
@click.option('--inpaths', '-i', multiple=True, default=[BAREFOOT_CONTESSA_JSON, OH_SHE_GLOWS_JSON])
@click.option('--outpath', '-o', type=str, default='open_ai/data')
def main(inpaths, outpath):
    for inpath in inpaths:
        out_fn = get_file_name(inpath, '_w_nutrients')

        if not os.path.isdir(outpath):
            raise Exception(f'{outpath} is not a directory')

        outpath = f'{outpath}/{out_fn}'

        with open(inpath, 'r') as file:
            recipes = json.loads(file.read())
            with Pool(5) as p:
                p.map(partial(add_protein_data, outpath=outpath), recipes)

if __name__ == "__main__":
    main()

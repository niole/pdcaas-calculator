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
from create_food_info_vector_tables import create_recipe_upserts, upload_chunks
from get_gram_weight import get_gram_weight
from models.amino_acid import AminoAcid
from models.ingredient import Ingredient as IngredientModel
from models.recipe import Recipe as RecipeModel
from sqlalchemy.orm import Session
from sqlalchemy import delete
from add_recipes_to_db import create_models
from engine import *

from dotenv import load_dotenv
load_dotenv()

logger = multiprocessing.get_logger()
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

model = SentenceTransformer('./transformers/vegan_improved_food_item_transformer')

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
    logger.warning(f"Computing protein data for recipe {recipe['title']}")

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

            ingredient = IngredientModel(
                food_query,
                food_match_name,
                food_match_id,
                td_score,
                total_protein_ing_g,
                measure_amount_query,
                measure_units_query,
                [AminoAcid(f['name'], gram_weight*f['per100g']/100) for f in aas]
            )

            ingredients.append(ingredient)
            break

    scored_recipe = RecipeModel(
        id=recipe["id"],
        title=recipe["title"],
        instructions=recipe["instructions"],
        ingredients=ingredients,
        raw_ingredients=recipe["ingredients"]
    )

    if len(ingredients) < len(recipe['ingredients_w_units']) or not scored_recipe.is_scored():
        logger.warning(f"Failed to score all ingredients in recipe {recipe['title']}")

        # TODO update database entry with scoring data from scored_recipe

    return scored_recipe

"""
Computes the protein breakdown for a recipe by finding a nutrient vector match
"""
def add_protein_data(recipe):
    try:
        scored_recipe = cli(recipe).to_json()
        recipe_models = create_models(scored_recipe)
        recipe_model = recipe_models[0]

        with Session(engine) as session:
            session.add_all([recipe_model])
            session.commit()

            scored_recipe['id'] = str(recipe_model.id)

            vector_data = create_recipe_upserts([scored_recipe], model)
            return (recipe_models, vector_data[0])

    except Exception as e:
        traceback.print_exc()
        logger.error(f'Something went wrong when getting protein data for {recipe["title"]}: {e}')
        return None

@click.command()
@click.option('--inpaths', '-i', multiple=True, default=[BAREFOOT_CONTESSA_JSON, OH_SHE_GLOWS_JSON])
@click.option('--delete', '-d', is_flag=True, required=False, default=False, help="Whether or not to delete the recipe data in sql and vector db at the start")
def main(inpaths, delete):
    if delete:
        print("DELETING")
        # delete everything in recipes vector db and sql db
        index = pinecone.Index("food")
        index.delete(delete_all=True, namespace='recipes')

        with Session(engine) as session:
            session.query(Recipe).delete(synchronize_session=False)
            session.query(RawIngredient).delete(synchronize_session=False)
            session.query(Ingredient).delete(synchronize_session=False)
            session.query(IngredientAminoAcid).delete(synchronize_session=False)
            session.query(RecipeAminoAcid).delete(synchronize_session=False)
            session.commit()

    for inpath in inpaths:
        with open(inpath, 'r') as file:
            recipes = json.loads(file.read())
            with Pool(5) as p:
                results = [r for r in p.map(partial(add_protein_data), recipes) if r is not None]

                # TODO update the vector data to put ids in the vector id
                vector_data = [r[1] for r in results]
                upload_chunks(vector_data, 'recipes')

if __name__ == "__main__":
    main()

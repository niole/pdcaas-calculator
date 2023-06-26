import os
import json
from sentence_transformers import SentenceTransformer
import pinecone
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()

from test_recipes.veganmacandcheese import recipe as veganmacandcheese
from test_recipes.cup_of_soymilk import recipe as soymilk_recipe
from pinecone_client import find_limit_vector_query, find_one_vector_query

model = SentenceTransformer('all-MiniLM-L6-v2')

essential_amino_acids = ["Tryptophan","Threonine","Isoleucine","Leucine","Lysine","Methionine","Phenylalanine","Valine","Histidine"]
EAAS_QUERY_STRING = ','.join(["'" + a + "'" for a in essential_amino_acids])
EAA_PROPORTIONS = {
    "Tryptophan": 7/1000,
    "Threonine": 27/1000,
    "Isoleucine": 25/1000,
    "Leucine": 55/1000,
    "Lysine": 51/1000,
    "Methionine": 25/1000,
    "Phenylalanine": 47/1000,
    "Valine": 32/1000,
    "Histidine": 18/1000
}

def create_aa(name, total_per100g, total_g_ing):
    return {
        'name': name,
        'total_protein_g': total_g_ing*total_per100g/100
    }
def create_ingredient(food_query, name, total_protein, td = 1, aas = []):
    return {
        'name': name,
        'food_query': food_query,
        'aas': aas,
        'total_protein_g': total_protein,
        'td': td
    }

def set_td(ingredient, td_score):
    # set TD score for ingredient
    ingredient['td'] = td_score

def create_initial_ingredient(food_query, name, total_protein, total_g_ing, aas):
    aas_final = []

    for f in aas:
        aas_final.append(
            create_aa(f['name'], f['per100g'], total_g_ing)
        )
    ingredient = create_ingredient(food_query, name, total_protein, 1, aas_final)

    return ingredient

def get_limiting_aa(ingredient):
    # calculating percentage complete protein
    # if an aa comes in low w/ respect to total protein, then it is a limiting factor
    # a limiting aa is one that when considered in proportion to the total amount of protein, has the lowest score

    total_protein_g = ingredient['total_protein_g']
    percent_expected = []
    print(ingredient['name'])
    print(ingredient['aas'])
    for aa in ingredient['aas']:
        # the expected proportion of the ingredients protein in order for it to be complete
        expected = EAA_PROPORTIONS[aa['name']]*ingredient['total_protein_g']
        actual = aa['total_protein_g']
        if actual > 0 and expected > 0:
            percent_expected.append((aa['name'], actual/expected))
        else:
            percent_expected.append((aa['name'], 0))

    if len(percent_expected) > 0:
        limiting_aa = min(percent_expected, key = lambda k: k[1])[0]
        return next((a for a in ingredient['aas'] if a['name'] == limiting_aa), None)
    return None

"""
This calculates the protein balance for all ingredients and returns the percent of consumed
protein that is digestible and balanced protein from the essential amino acids.
"""
def calculated_percent_digestible_protein(ingredients):
    total_achievable_protein_g = 0
    protein_g = 0
    ingredient_summaries = []

    if len(ingredients) == 0:
        return 0

    for ingredient in ingredients:
        limiting_aa_details = get_limiting_aa(ingredient)
        limiting_aa = None
        total_limiting_aa_g = 0
        total_achievable_protein_food_g = 0

        if limiting_aa_details:
            limiting_aa = limiting_aa_details['name']

            # calculate the total digestible complete protein by dividing the limiting aa by its proportion
            total_limiting_aa_g = limiting_aa_details['total_protein_g']
            total_achievable_protein_food_g = ingredient['td'] * min(total_limiting_aa_g / EAA_PROPORTIONS[limiting_aa], ingredient['total_protein_g'])
        ingredient_summaries.append({
            'name': ingredient['name'],
            'limiting_aa_details': limiting_aa_details,
            'total_protein_g': ingredient['total_protein_g'],
            'total_balanced_protein_g': total_achievable_protein_food_g,
            'aas': ingredient['aas'],
        })

        total_achievable_protein_g += total_achievable_protein_food_g
        protein_g += ingredient['total_protein_g']

    return {
        "percent_complete_digestible_protein": total_achievable_protein_g/protein_g,
        "total_complete_digestible_protein_g": total_achievable_protein_g,
        "total_protein_g": protein_g,
        "ingredient_summaries": ingredient_summaries,
    }


def get_matching_food_items(query):
    ms = list(find_limit_vector_query(query, 20, 'info'))

    return [m for m in ms if m['score'] >= 0.6]

def get_measure_conversion(requested_units, units):
    """
    get the conversion multipler to go from total units to the equivalent number of requested_units
    """
    matches = find_limit_vector_query(requested_units, 5, 'measures')
    for match in matches:
        if match['id'] == units or match['id'] in requested_units:
            return 1
    return None
"""
This calculates the proportion of protein that is digestible complete protein.
This is calculated for 1 ingredient, however it can be extrapolated to multiple meals.

This takes the gram weight of an ingredient, the gram weight of protein per 100 g of that ingredient,
and the gram weight of each essential amino acid per 100g of that ingredient, and then
the total digestibility score of that ingredient as inputs.
"""


"""
Recipe generation prompt:
give me a recipe for vegan mac and cheese for 1 person. give me the recipe in the following format, JSON only: { "total_servings": 5,  "ingredients": [{"units": "cup", "name": "wheat pasta", "total": 1}, {"units":"tsp", "name":"salt","total": 0.5}, {"units": "lbs", "name": "beef", "total": 1}, {"units": "teaspoon", "name": "mustard", "total": 0.25}, {"units": "tablespoon", "name":"peanut butter", "total": 2}, {"units":"tbsp", "name":"sour cream", "total":1.5}], "instructions": "Boil the pasta for 11 minutes with the salt in water. Serve immediately."}

Recipe name generation prompt:
generate the names of 20 vegan breakfast meals. give the output in the following format, JSON only: ["the name of meal 1", "the name of meal 2", "the name of meal 3"]

pre-generate a bunch of recipes and their amino acid balances

Let the user also put in their own meal names. We can then recommend snacks to round out their amino acid balance.
User can scale the recipes according to their calorie needs through a UI and then we can give better info about total digestible balanced protein. TODO Do we have calorie data?
"""
def cli(recipe):
    """
    for each ingredient in a recipe, find the food entry that best matches it, the td_types entry that best matches it,
    and compute the gram weight

    computing gram weight: if there is a weight entry in cup, tsp, teaspoon, tbsp, tablespoon, we can probably work with that
    find closest match for ingredient in food_info or td_types: put all food names into a collection in a vector db and all td_types in their own collection
    and do a search
    """
    ingredients = []
    for ing in recipe['ingredients']:
        food_query = ing['name']
        measure_units_query = ing['units']
        measure_amount_query = ing['total']


        # each food item has it's name, id, per 100g stats for protein and amino acids, and the td score
        food_items = get_matching_food_items(food_query)

        if len(food_items) == 0:
            print(f"Couldn't find a matching food item for query {food_query}")
            print()
            continue

        for food_item in food_items:
            id = food_item['id']
            metadata = food_item['metadata']
            food_name = metadata['tmp_name']
            aas = [json.loads(a) for a in metadata['aas']]
            weights = [json.loads(w) for w in metadata['weights']]

            td_score = None
            if 'td_score' in metadata:
                td_score = metadata['td_score']

            ingredient = None
            measure_units = measure_units_query
            gram_weight = None

            protein_per_100g = metadata['protein_per_100g']

            for weight in weights:
                conversion = get_measure_conversion(measure_units_query, weight['Msre_Desc'])
                if conversion is not None:
                    gram_weight = conversion * weight['Gm_Wgt'] * measure_amount_query
                    break

            if gram_weight is None:
                print(f"Insufficient weight data. Can't convert {measure_amount_query} {measure_units_query} of {food_query} to grams.")
                continue

            # calculate total protein grams in queried amount of food
            total_protein_ing = gram_weight*protein_per_100g/100

            ingredient = create_initial_ingredient(food_name, food_query, total_protein_ing, gram_weight, aas)
            ingredient['amount'] = measure_amount_query
            ingredient['unit'] = measure_units_query

            if td_score is not None:
                set_td(ingredient, td_score)

            if ingredient is not None:
                ingredients.append(ingredient)
                break

    percent_digestible_complete_protein = calculated_percent_digestible_protein(ingredients)
    return percent_digestible_complete_protein

if __name__ == "__main__":
    recipe = veganmacandcheese #soymilk_recipe
    percent_digestible_complete_protein = cli(recipe)
    print("Total Protein Stats")
    pprint(percent_digestible_complete_protein)

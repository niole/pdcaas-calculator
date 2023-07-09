import os
import re
import click
from functools import partial
import json
import logging
from sentence_transformers import SentenceTransformer
import pinecone
from pprint import pprint
from multiprocessing import Pool
import multiprocessing
from pinecone_client import find_limit_vector_query, find_one_vector_query
from conversions_map import CONVERSIONS, LB_GROUP, OUNCE_GROUP
from get_file_name import get_file_name
from dotenv import load_dotenv
load_dotenv()

logger = multiprocessing.get_logger()
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1') # pretty good, still off

BAREFOOT_CONTESSA_JSON = 'open_ai/data/barefootcontessa_array.json'
OH_SHE_GLOWS_JSON = 'open_ai/data/ohsheglows_array.json'

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
def create_ingredient(id, food_item_name, name, total_protein, td = 1, aas = []):
    return {
        'name': name,
        'food_match': {
            'id': id,
            'name': food_item_name,
        },
        'aas': aas,
        'total_protein_g': total_protein,
        'td': td
    }

def set_td(ingredient, td_score):
    # set TD score for ingredient
    ingredient['td'] = td_score

def create_initial_ingredient(id, food_item_name, name, total_protein, total_g_ing, aas):
    aas_final = []

    for f in aas:
        aas_final.append(
            create_aa(f['name'], f['per100g'], total_g_ing)
        )
    ingredient = create_ingredient(id, food_item_name, name, total_protein, 1, aas_final)

    return ingredient

def get_limiting_aa(ingredient):
    # calculating percentage complete protein
    # if an aa comes in low w/ respect to total protein, then it is a limiting factor
    # a limiting aa is one that when considered in proportion to the total amount of protein, has the lowest score

    total_protein_g = ingredient['total_protein_g']
    percent_expected = []
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
output:
{
    "percent_complete_digestible_protein": number,
    "total_complete_digestible_protein_g": number,
    "total_protein_g": number,
    "ingredient_summaries": {
        'name': string,
        'food_match': { id: string, name: string },
        'limiting_aa_details': {
            'name': string,
            'total_protein_g': number
        },
        'total_protein_g': number,
        'total_balanced_protein_g': number,
        'aas': {
            'name': string,
            'total_protein_g': number
        }[]
    }[]
}
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
            'food_match': ingredient['food_match'],
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

    return [m for m in ms if m['score'] >= 0.55]

"""
requested_units - the units that are found in the recipe
units - units that we have a "to grams" conversion for with regards to the food item that corresponds to the ingredient

returns - a scalar, with which to multiply the ingredient's quantity in order to convert it from "requested_units" to "units"
"""
def get_measure_conversion(requested_units, units):
    # check to see if the requested units could be real
    likely_measures = find_limit_vector_query(requested_units, 5, 'measures')
    match = next((m for m in likely_measures if m['score'] >= 0.7), None)
    # check to see if the found
    # weight matches the known weights
    if match is not None:
        matched_unit = match['id']

        if matched_unit in CONVERSIONS:
            conversions = CONVERSIONS[matched_unit]
            conversion = next(
                (c for c in conversions if c[0] == units),
                None
            )
            if conversion is not None:
                return conversion[1]
            else:
                # convert straight to grames, even though might be inaccurate
                direct_grams_conversion = next((c for c in conversions if c[0] == 'g'), None)
                if direct_grams_conversion is not None:
                    return direct_grams_conversion[1]

    return None

"""
Gets the weight in grams of the ingredient

ingredient_units  -  The units of the ingredient in the recipe
ingredient_amount - The amount of the ingredient in the recipe
possible_measure_unit - Units of a measure that we have a conversion to grams for this ingredient
possible_measure_weight - The weight of 1 unit of the possible measure in grams

returns - the weight in grams of this ingredient
"""
def get_gram_weight(food_name, ingredient_units, ingredient_amount, possible_measure_unit, possible_measure_weight):
    logger.warning(f"get_gram_weight {food_name}, {ingredient_units}, {ingredient_amount}, {possible_measure_unit}, {possible_measure_weight}")
    conversion = get_measure_conversion(ingredient_units, possible_measure_unit)
    if conversion is not None:
        return conversion * possible_measure_weight * ingredient_amount
    else:
        # TODO do 1 off checks against food_name
        is_bread = re.search(r'bread', food_name, re.IGNORECASE)
        is_bacon = re.search(r'bacon', food_name, re.IGNORECASE)
        is_egg = re.search(r'egg', food_name, re.IGNORECASE)
        is_yolk = re.search(r'yolk', food_name, re.IGNORECASE)
        is_white = re.search(r'white', food_name, re.IGNORECASE)
        is_slice = re.search(r'slice', ingredient_units, re.IGNORECASE)

        if is_bacon and is_slice:
            # a slice of bacon is 12 grams
            return 12 * ingredient_amount
        elif is_egg:
            if is_white:
                return 33 * ingredient_amount 
            elif is_yolk:
                return 17 * ingredient_amount 
            else:
                return 50 * ingredient_amount 
        elif is_bread and is_slice:
            return 30 * ingredient_amount 

    return None

"""
This calculates the proportion of protein that is digestible complete protein.
This is calculated for 1 ingredient, however it can be extrapolated to multiple meals.

This takes the gram weight of an ingredient, the gram weight of protein per 100 g of that ingredient,
and the gram weight of each essential amino acid per 100g of that ingredient, and then
the total digestibility score of that ingredient as inputs.
"""
def cli(recipe):
    """
    for each ingredient in a recipe, find the food entry that best matches it, the td_types entry that best matches it,
    and compute the gram weight

    computing gram weight: if there is a weight entry in cup, tsp, teaspoon, tbsp, tablespoon, we can probably work with that
    find closest match for ingredient in food_info or td_types: put all food names into a collection in a vector db and all td_types in their own collection
    and do a search
    """
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
            id = food_item['id']
            metadata = food_item['metadata']
            food_name = metadata['tmp_name']

            logger.warning(f"Found food item match for request {food_query}: {food_name}, id {id}")

            aas = [json.loads(a) for a in metadata['aas']]
            weights = [json.loads(w) for w in metadata['weights']]

            td_score = None
            if 'td_score' in metadata:
                td_score = metadata['td_score']

            ingredient = None
            gram_weight = None

            protein_per_100g = metadata['protein_per_100g']

            for weight in weights:
                gram_weight = get_gram_weight(food_query, measure_units_query, measure_amount_query, weight['Msre_Desc'], weight['Gm_Wgt'])
                if gram_weight is not None:
                    break

            if gram_weight is None:
                logger.warning(f"Insufficient weight data. Can't convert {food_query} measurement to grams, units: {measure_amount_query}, amount: {measure_units_query}.")
                continue

            # calculate total protein grams in queried amount of food
            total_protein_ing = protein_per_100g*gram_weight/100

            ingredient = create_initial_ingredient(id, food_name, food_query, total_protein_ing, gram_weight, aas)
            ingredient['amount'] = measure_amount_query
            ingredient['unit'] = measure_units_query

            if td_score is not None:
                set_td(ingredient, td_score)

            if ingredient is not None:
                ingredients.append(ingredient)
                break

    percent_digestible_complete_protein = calculated_percent_digestible_protein(ingredients)
    return percent_digestible_complete_protein

def add_protein_data(recipe, outpath):
    try:
        protein_breakdown = cli(recipe)
        recipe['nutrient_breakdown'] = { 'protein_breakdown': protein_breakdown }
        with open(outpath, 'a') as outfile:
            outfile.write(json.dumps(recipe))
    except Exception as e:
        logger.error(f'Something went wrong when getting protein data for {recipe["title"]}: {e}')

def test_get_gram_weight():
    food_name = 'sugar'
    actual = get_gram_weight(food_name, 'oz', 8, 'g', 10)
    expected = 28.34 * 8 * 10
    assert(actual == expected)

    actual2 = get_gram_weight(food_name, 'tsps', 2.5, 'cups', 4)
    expected2 = 1/48 * 2.5 * 4
    assert(actual2 == expected2)

    actual3 = get_gram_weight(food_name, 'cup', 2.5, 'teaspoon', 4)
    expected3 = 48 * 2.5 * 4
    assert(actual3 == expected3)

    actual4 = get_gram_weight(food_name, 'tablespoon', 2.5, 'tsp', 4)
    expected4 = 3 * 2.5 * 4
    assert(actual4 == expected4)

    actual5 = get_gram_weight(food_name, 'g', 8, 'ounces', 10)
    expected5 = 1/28.34 * 8 * 10
    assert(actual5 == expected5)

    actual6 = get_gram_weight(food_name, 'pound', 8, 'ounce', 10)
    expected6 = 16 * 8 * 10
    assert(actual6 == expected6)

    actual7 = get_gram_weight(food_name, 'oz', 8, 'lb', 10)
    expected7 = 1/16 * 8 * 10
    assert(actual7 == expected7)

    actual8 = get_gram_weight('brocolini', 'pounds', 5.5, 'grams', 1)
    expected8 = 453.6 * 5.5
    assert(actual8 == expected8)


#if __name__ == '__main__':
#    test_get_gram_weight()


#if __name__ == '__main__':
#    recipe = {'title': 'Broccoli & Bow Ties (updated)', 'yields': 'Serves 6 to 8', 'ingredients': ['Kosher salt', '8 cups broccoli florets (4 heads)', '1/2 pound farfalle (bow tie) pasta', '3 tablespoons unsalted butter', '3 tablespoons good olive oil', '1 teaspoon minced garlic', 'Zest of 1 lemon', '1/2 teaspoon freshly ground black pepper', '1 tablespoon freshly squeezed lemon juice', '1/4 cup toasted pignoli (pine) nuts', 'Freshly grated Parmesan cheese, optional'], 'instructions': 'Cook the broccoli for 3 minutes in a large pot of boiling salted water. Remove the broccoli from the water with a slotted spoon or sieve. Place in a large bowl and set aside. In the same water, cook the bow-tie pasta according to the package directions, about 12 minutes. Drain well and add to the broccoli. Meanwhile, in a small saute pan, heat the butter and oil and cook the garlic and lemon zest over medium-low heat for 1 minute. Off the heat, add 2 teaspoons salt, the pepper, and lemon juice and pour this over the broccoli and pasta. Toss well. Season to taste, sprinkle with the pignolis and cheese, if using, and serve.', 'description': 'classic american comfort food. There’s nothing like a home-cooked meal to make everyone feel happy and loved.', 'tags': [], 'id': 'e08768c27f73d7824c9e80a53a8c6e7d', 'ingredients_w_units': [{'units': 'Kosher salt', 'name': '8 cups broccoli florets (4 heads)', 'total': 8}, {'units': 'pound', 'name': 'farfalle (bow tie) pasta', 'total': 0.5}, {'units': 'tablespoons', 'name': 'unsalted butter', 'total': 3}, {'units': 'tablespoons', 'name': 'good olive oil', 'total': 3}, {'units': 'teaspoon', 'name': 'minced garlic', 'total': 1}, {'units': 'Zest of 1 lemon', 'name': '0.5 teaspoon freshly ground black pepper', 'total': 0.5}, {'units': 'tablespoon', 'name': 'freshly squeezed lemon juice', 'total': 1}, {'units': 'cup', 'name': 'toasted pignoli (pine) nuts', 'total': 0.25}, {'units': 'Freshly grated Parmesan cheese, optional', 'name': '', 'total': 0}]}
#    pprint(recipe)
#    protein_breakdown = cli(recipe)
#    pprint(protein_breakdown)

def cli_test():
    r1 = {"title":"Country French Omelet","yields":"Serves 2","ingredients":["1 \ttablespoon good olive oil","3\t slices thick-cut bacon, cut into 1-inch pieces","1 \tcup (1-inch-diced) unpeeled Yukon Gold potatoes","Kosher salt and freshly ground black pepper","5 \textra-large eggs","3 \ttablespoons milk","1\t tablespoon unsalted butter","1\t tablespoon fresh chopped chives"],"instructions":"Preheat the oven to 350 degrees. Heat the olive oil in a 10-inch ovenproof omelet pan over medium heat. Add the bacon and cook for 3 to 5 minutes over medium-low heat, stirring occasionally, until the bacon is browned but not crisp. Take the bacon out of the pan with a slotted spoon and set aside on a plate. Place the potatoes in the pan and sprinkle with salt and pepper. Continue to cook over medium-low heat for 8 to 10 minutes, until very tender and browned, tossing occasionally to brown evenly. Remove with a slotted spoon to the same plate with the bacon. Meanwhile, in a medium bowl, beat the eggs, milk, 1/2 teaspoon salt, and 1/4 teaspoon pepper together with a fork. After the potatoes are removed, pour the fat out of the pan and discard. Add the butter, lower the heat to low, and pour the eggs into the hot pan. Sprinkle the bacon, potatoes, and chives evenly over the top and place the pan in the oven for about 8 minutes, just until the eggs are set. Slide onto a plate, divide in half, and serve hot.","description":"classic american comfort food. There’s nothing like a home-cooked meal to make everyone feel happy and loved.","tags":["breakfast","brunch","French","Weeknight","Easy","Gluten Free","eggs","bacon"],"id":"3a84aa9d5a21322374f6a1dde57db4ad","ingredients_w_units":[{"units":"tablespoon","name":"olive oil","total":1},{"units":"slices","name":"bacon","total":3},{"units":"cup","name":"Yukon Gold potatoes","total":1},{"units":"extra-large","name":"eggs","total":5},{"units":"tablespoon","name":"milk","total":3},{"units":"tablespoon","name":"unsalted butter","total":1},{"units":"tablespoon","name":"chopped chives","total":1}],"nutrient_breakdown":{"protein_breakdown":{"percent_complete_digestible_protein":0.5199551050052298,"total_complete_digestible_protein_g":2.7652187400000003,"total_protein_g":5.3181875,"ingredient_summaries":[{"name":"olive oil","limiting_aa_details":{"name":"Histidine","total_protein_g":0},"total_protein_g":0,"total_balanced_protein_g":0,"aas":[{"name":"Histidine","total_protein_g":0},{"name":"Isoleucine","total_protein_g":0},{"name":"Leucine","total_protein_g":0},{"name":"Lysine","total_protein_g":0},{"name":"Methionine","total_protein_g":0},{"name":"Phenylalanine","total_protein_g":0},{"name":"Threonine","total_protein_g":0},{"name":"Tryptophan","total_protein_g":0},{"name":"Valine","total_protein_g":0}]},{"name":"Yukon Gold potatoes","limiting_aa_details":{"name":"Methionine","total_protein_g":0.07332},"total_protein_g":4.68,"total_balanced_protein_g":2.316912,"aas":[{"name":"Methionine","total_protein_g":0.07332},{"name":"Tryptophan","total_protein_g":0.07332},{"name":"Histidine","total_protein_g":0.10452},{"name":"Threonine","total_protein_g":0.17004000000000002},{"name":"Isoleucine","total_protein_g":0.19188},{"name":"Phenylalanine","total_protein_g":0.20748},{"name":"Valine","total_protein_g":0.26208000000000004},{"name":"Leucine","total_protein_g":0.28236},{"name":"Lysine","total_protein_g":0.28392}]},{"name":"milk","limiting_aa_details":{"name":"Methionine","total_protein_g":0.00968625},"total_protein_g":0.4750875,"total_balanced_protein_g":0.3758265,"aas":[{"name":"Tryptophan","total_protein_g":0.007841250000000001},{"name":"Methionine","total_protein_g":0.00968625},{"name":"Histidine","total_protein_g":0.01060875},{"name":"Phenylalanine","total_protein_g":0.0212175},{"name":"Threonine","total_protein_g":0.0212175},{"name":"Isoleucine","total_protein_g":0.025830000000000002},{"name":"Valine","total_protein_g":0.02905875},{"name":"Lysine","total_protein_g":0.031365000000000004},{"name":"Leucine","total_protein_g":0.04381875}]},{"name":"unsalted butter","limiting_aa_details":{"name":"Methionine","total_protein_g":0.0029820000000000003},"total_protein_g":0.12069999999999999,"total_balanced_protein_g":0.0679896,"aas":[{"name":"Tryptophan","total_protein_g":0.001704},{"name":"Methionine","total_protein_g":0.0029820000000000003},{"name":"Histidine","total_protein_g":0.003266},{"name":"Threonine","total_protein_g":0.005396},{"name":"Phenylalanine","total_protein_g":0.005822000000000001},{"name":"Isoleucine","total_protein_g":0.007241999999999999},{"name":"Valine","total_protein_g":0.008094},{"name":"Lysine","total_protein_g":0.009514},{"name":"Leucine","total_protein_g":0.011786000000000001}]},{"name":"chopped chives","limiting_aa_details":{"name":"Methionine","total_protein_g":0.00046200000000000006},"total_protein_g":0.0424,"total_balanced_protein_g":0.00449064,"aas":[{"name":"Methionine","total_protein_g":0.00046200000000000006},{"name":"Tryptophan","total_protein_g":0.000474},{"name":"Histidine","total_protein_g":0.000732},{"name":"Phenylalanine","total_protein_g":0.0013640000000000002},{"name":"Threonine","total_protein_g":0.001662},{"name":"Isoleucine","total_protein_g":0.0017980000000000001},{"name":"Valine","total_protein_g":0.0018720000000000004},{"name":"Lysine","total_protein_g":0.0021160000000000003},{"name":"Leucine","total_protein_g":0.00253}]}]}}}

#    actual1 = cli(r1)
#    pprint(actual1)

    r2 = {"title":"Roasted Broccolini & Cheddar","yields":"Serves 4","ingredients":["11/2 pounds broccolini","Good olive oil","Kosher salt and freshly ground black pepper","6 ounces good sharp aged white Cheddar, such as Cabot","Juice of 1/2 lemon"],"instructions":"Preheat the oven to 400 degrees. Remove and discard the bottom half of the broccolini stems. Cut the remaining broccolini stems in half or quarters lengthwise, depending on the size of the stems. Don't cut the florets-just pull them apart. Place the broccolini on a sheet pan. Drizzle 4 tablespoons olive oil on the broccolini and sprinkle with 1 teaspoon salt and 1/2 teaspoon pepper. Toss well, making sure the broccolini is lightly coated with oil. Spread the broccolini in one layer and roast for 10 minutes, tossing once with a metal spatula, until crisp-tender. Meanwhile, slice the Cheddar 1/4 inch thick and break it into large crumbles. When the broccolini is ready, sprinkle the cheese on the broccolini and return to the oven for 3 to 4 minutes, just until the cheese melts. Squeeze on the lemon juice, taste for seasonings, and serve hot.","description":"classic american comfort food. There’s nothing like a home-cooked meal to make everyone feel happy and loved.","tags":["broccolini","Vegetarian","Easy","moderncomfortfood"],"id":"69eeb6f8c52841b759fc2ccc78ac1ffd","ingredients_w_units":[{"units":"pounds","name":"broccolini","total":5.5},{"units":"tsp","name":"good olive oil","total":1},{"units":"tsp","name":"kosher salt and freshly ground black pepper","total":0.5},{"units":"ounces","name":"good sharp aged white Cheddar, such as Cabot","total":6},{"units":"tsp","name":"juice of 0.5 lemon","total":0.5}],"nutrient_breakdown":{"protein_breakdown":{"percent_complete_digestible_protein":0,"total_complete_digestible_protein_g":0,"total_protein_g":0.051691666666666664,"ingredient_summaries":[{"name":"good olive oil","limiting_aa_details":{},"total_protein_g":0.018500000000000003,"total_balanced_protein_g":0,"aas":[]},{"name":"kosher salt and freshly ground black pepper","limiting_aa_details":{},"total_protein_g":0.02144166666666666,"total_balanced_protein_g":0,"aas":[]},{"name":"juice of 0.5 lemon","limiting_aa_details":{},"total_protein_g":0.011749999999999998,"total_balanced_protein_g":0,"aas":[]}]}}}
    actual2 = cli(r2)
    pprint(actual2)

#if __name__ == "__main__":
#    cli_test()

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

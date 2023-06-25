from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session
import pinecone
from test_recipes.veganmacandcheese import recipe as veganmacandcheese


model = SentenceTransformer('all-MiniLM-L6-v2')
pinecone.init(api_key="fc70e073-5679-4bcf-a009-38f0e42e09e2", environment="northamerica-northeast1-gcp")
index = pinecone.Index("food")

engine = create_engine(
    "sqlite:///food.db",
    #echo=True,
)

essential_amino_acids = ["Tryptophan","Threonine","Isoleucine","Leucine","Lysine","Methionine","Phenylalanine","Valine","Histidine"]
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

def create_ingredient(food_query, name, total_protein, td = 1, aas = []):
    return {
        'name': name,
        'food_query': food_query,
        'aas': aas,
        'total_protein_g': total_protein,
        'td': td
    }

def create_aa(name, total_per100g, total_g_ing):
    return {
        'name': name,
        'total_protein_g': total_g_ing*total_per100g/100
    }

def set_td(ingredient, td_score):
    # set TD score for ingredient
    ingredient['td'] = td_score

def create_initial_ingredient(food_query, name, total_protein, total_g_ing, aa_rows):
    ingredient = create_ingredient(food_query, name, total_protein)

    for f in aa_rows:
        ingredient['aas'].append(
            create_aa(f.NutrDesc, f.Nutr_Val, total_g_ing)
        )
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
        percent_expected.append((aa['name'], actual/expected))

    limiting_aa = min(percent_expected, key = lambda k: k[1])[0]
    return next((a for a in ingredient['aas'] if a['name'] == limiting_aa), None)

"""
This calculates the protein balance for all ingredients and returns the percent of consumed
protein that is digestible and balanced protein from the essential amino acids.
"""
def calculated_percent_digestible_protein(ingredients):
    total_achievable_protein_g = 0
    protein_g = 0

    if len(ingredients) == 0:
        return 0

    for ingredient in ingredients:
        limiting_aa_details = get_limiting_aa(ingredient)
        limiting_aa = limiting_aa_details['name']

        # calculate the total digestible complete protein by dividing the limiting aa by its proportion
        total_limiting_aa_g = limiting_aa_details['total_protein_g']
        total_achievable_protein_food_g = ingredient['td'] * min(total_limiting_aa_g / EAA_PROPORTIONS[limiting_aa], ingredient['total_protein_g'])

        print(f"{ingredient['name']}")
        print(f"Limiting amino acid: {limiting_aa}")
        print(f"Total achievable protein: {total_achievable_protein_food_g}, out of total protein: {ingredient['total_protein_g']}, in {ingredient['amount']} {ingredient['unit']}")
        print()

        total_achievable_protein_g += total_achievable_protein_food_g
        protein_g += ingredient['total_protein_g']

    return total_achievable_protein_g / protein_g

def find_limit_vector_query(query, limit, namespace):
    matches = index.query(
        vector=model.encode(query).tolist(),
        top_k=limit,
        include_values=True,
        namespace=namespace
    )['matches']

    return matches

def find_one_vector_query(query, namespace):
    matches = index.query(
        vector=model.encode(query).tolist(),
        top_k=1,
        include_values=True,
        namespace=namespace
    )['matches']

    if len(matches) == 0:
        return None

    return matches[0]

def get_matching_food_item(query):
    match = find_one_vector_query(query, 'info')

    return match['id']

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
def cli(conn):
    """
    for each ingredient in a recipe, find the food entry that best matches it, the td_types entry that best matches it,
    and compute the gram weight

    computing gram weight: if there is a weight entry in cup, tsp, teaspoon, tbsp, tablespoon, we can probably work with that
    find closest match for ingredient in food_info or td_types: put all food names into a collection in a vector db and all td_types in their own collection
    and do a search
    """
    recipe = veganmacandcheese
    ingredients = []
    for ing in recipe['ingredients']:
        food_query = ing['name']
        measure_units_query = ing['units']
        measure_amount_query = ing['total']

        ingredient = None
        measure_units = measure_units_query
        gram_weight = None

        NDB_No = get_matching_food_item(food_query)

        if NDB_No is None:
            print(f"Couldn't find a matching food item for query {food_query}")
            print()
            continue

        result = conn.execute(
            text("select * from food_info_types where NDB_No = :id and NutrDesc = 'Protein' limit 1"),
            {'id': NDB_No}
        )

        for row in result:
            id = row.NDB_No
            protein_per_100g = row.Nutr_Val

            if protein_per_100g is None or protein_per_100g == 0:
                print(f"{food_query} doesn't contain protein. Skipping.")
                print()
                continue

            aas = ','.join(["'" + a + "'" for a in essential_amino_acids])


            food = conn.execute(
                    text("select distinct * from food_info_types where NDB_No = :id and NutrDesc in ("+aas+")"),
                    {'id': id }
            )

            measure_result = conn.execute(
                text('select * from weight where NDB_No = :id'),
                { 'id': id }
            )

            for weight in measure_result:
                # TODO might have to do some adjustment here
                #  might have to adjust the measure amount and the units
                conversion = get_measure_conversion(measure_units_query, weight.Msre_Desc)
                if conversion is not None:
                    gram_weight = conversion * weight.Gm_Wgt * measure_amount_query
                    break

            if gram_weight is None:
                print(f"Insufficient weight data. Can't convert {measure_amount_query} {measure_units_query} of {food_query} to grams.")
                continue

            if gram_weight == None:
                raise Exception('Couldnt compute gram weight of ingredient')


            # calculate total protein grams in queried amount of food
            total_protein_ing = gram_weight*protein_per_100g/100

            ingredient = create_initial_ingredient(row.Long_Desc, food_query, total_protein_ing, gram_weight, food)
            ingredient['amount'] = measure_amount_query
            ingredient['unit'] = measure_units_query

            if len(ingredient['aas']) < 9:
                raise Exception("Not enough amino acid data")
            else:
                td_result = find_one_vector_query(food_query, 'td')

                if td_result is not None:
                    score_result = conn.execute(
                            text("select * from td_types where name = :name limit 1"),
                            {'name': td_result['id']}
                    )
                    for (_, score, _) in score_result:
                        set_td(ingredient, score)

            ingredients.append(ingredient)

    percent_digestible_complete_protein = calculated_percent_digestible_protein(ingredients)
    print(percent_digestible_complete_protein)

with Session(engine) as conn:
    cli(conn)

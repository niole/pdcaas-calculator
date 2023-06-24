from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session

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

        total_achievable_protein_g += ingredient['td'] * min(total_limiting_aa_g / EAA_PROPORTIONS[limiting_aa], ingredient['total_protein_g'])
        protein_g += ingredient['total_protein_g']

    return total_achievable_protein_g / protein_g

engine = create_engine(
    "sqlite:///food.db",
    #echo=True,
)

"""
This calculates the proportion of protein that is digestible complete protein.
This is calculated for 1 ingredient, however it can be extrapolated to multiple meals.

This takes the gram weight of an ingredient, the gram weight of protein per 100 g of that ingredient,
and the gram weight of each essential amino acid per 100g of that ingredient, and then
the total digestibility score of that ingredient as inputs.
"""

def cli(conn):
    food_query = 'soybean'
    measure_units_query = 'cup'
    measure_amount_query = 0.25

    ingredient = None
    measure_units = measure_units_query
    gram_weight = None

    result = conn.execute(
        text("select * from food_info_types where Long_Desc like '%" + food_query + "%' and NutrDesc = 'Protein' limit 1"),
    )

    for row in result:

        id = row.NDB_No
        print(id)
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
            if weight.Msre_Desc == measure_units_query:
                gram_weight = weight.Gm_Wgt *  measure_amount_query

        if gram_weight == None:
            raise Exception('Couldnt compute gram weight of ingredient')


        protein_per_100g = row.Nutr_Val
        # calculate total protein grams in queried amount of food
        total_protein_ing = gram_weight*protein_per_100g/100

        ingredient = create_initial_ingredient(row.Long_Desc, food_query, total_protein_ing, gram_weight, food)

        if len(ingredient['aas']) < 9:
            raise Exception("Not enough amino acid data")
        else:
            td_result = conn.execute(
                    text("select * from td_types where name like '%"+ food_query +"%' limit 1")
            )

            for (_, td_score, _) in td_result:
                set_td(ingredient, td_score)


            percent_digestible_complete_protein = calculated_percent_digestible_protein([ingredient])
            print(percent_digestible_complete_protein)

with Session(engine) as conn:
    cli(conn)

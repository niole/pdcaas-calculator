from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session

essential_amino_acids = ["Tryptophan","Threonine","Isoleucine","Leucine","Lysine","Methionine","Phenylalanine","Valine","Histidine"]
eaa_proportions = {
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

eea_factors = {}
total_factors = sum(eaa_proportions.values())
for (t,p) in eaa_proportions.items():
    eea_factors[t] = p/total_factors

def create_ingredient(name, total_protein, td = 1, aas = []):
    return {
        'name': name,
        'aas': aas,
        'total_protein_g': total_protein,
        'td': td
    }

def create_aa(name, total_per100g, total_protein_ing):
    return {
        'name': name,
        'per100g': total_per100g,
        'total_protein_g': total_protein_ing*total_per100g/100,
    }

def update_td(ingredient, td_score):
    # set TD score for ingredient
    ingredient['td'] = td_score

    # Apply TD score to each amino acid for ingredient
    for i in range(len(ingredient['aas'])):
        ingredient['aas'][i]['per100g'] *= td_score

    # Apply TD score to total protein
    ingredient['total_protein_g'] *= td_score

def create_initial_ingredient(name, total_protein, aa_rows):
    ingredient = create_ingredient(name, total_protein)

    for f in aa_rows:
        ingredient['aas'].append(
            create_aa(f.NutrDesc, f.Nutr_Val, total_protein)
        )
    return ingredient

def get_aa_g(ingredient):
    return ingredient['total_protein_g']*aa['per100g']/100

def get_limiting_aa(ingredient):
    # calculating percentage complete protein
    # if an aa comes in low w/ respect to total protein, then it is a limiting factor

    total_protein_g = ingredient['total_protein_g']
    total_aas = ingredient['aas']
    percent_expected = []
    for aa in total_aas:
        # the expected proportion of the ingredients protein in order for it to be complete
        expected = eaa_proportions[aa['name']]*ingredient['total_protein_g']
        actual = aa['total_protein_g']
        percent_expected.append((aa['name'], actual/expected))

    limiting_aa = min(percent_expected, key = lambda k: k[1])
    return  limiting_aa[0]

engine = create_engine(
    "sqlite:///food.db",
    #echo=True,
)

def cli(conn):
    food_query = 'soybean'
    result = conn.execute(
        text("select * from food_info_types where Long_Desc like '%" + food_query + "%' and NutrDesc = 'Protein' limit 1"),
    )

    for row in result:

        id = row.NDB_No
        aas = ','.join(["'" + a + "'" for a in essential_amino_acids])


        food = conn.execute(
                text("select distinct * from food_info_types where NDB_No = :id and NutrDesc in ("+aas+")"),
                {'id': id, 'aas': aas }
        )

        ingredient = create_initial_ingredient(food_query, row.Nutr_Val, food)

        if len(ingredient['aas']) < 9:
            raise Exception("Not enough amino acid data")
        else:
            td_result = conn.execute(
                    text("select * from td_types where name like '%"+ food_query +"%' limit 1")
            )

            for (_, td_score, _) in td_result:
                update_td(ingredient, td_score)

            limiting_aa = get_limiting_aa(ingredient)
            print(limiting_aa)

            # adjust the other amino acids to match the limiting one and then determine how many gs of complete protein that is
            aa_details = next((a for a in ingredient['aas'] if a['name'] == limiting_aa[0]), None)
            total_complete_protein = (ingredient['total_protein_g']*aa_details['per100g']/100) / eaa_proportions[aa['name']]
            print(total_complete_protein)

            # total amount of protein makeable is the limiting factor divided by it's proportion
            # total_protein = total_limiting_aa_protein / frac

with Session(engine) as conn:
    cli(conn)

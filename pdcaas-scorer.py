import click
import os
import pandas as pd

import functools
import json

NUTRIENT_CSV_DIR = os.environ['NUTRIENT_CSV_DIR']

NUTRIENT_DESC_COLUMN = 'NutrDesc'
USEFUL_COLUMNS = ['Shrt_Desc', 'NutrDesc', 'Nutr_No', 'FdGrp_Cd', 'N_Factor', 'Pro_Factor', 'Fat_Factor', 'CHO_Factor', 'Nutr_Val', 'NDB_No', 'Units', 'Tagname']
ESSENTIAL_AMINO_ACIDS = ['Tryptophan','Threonine','Isoleucine','Leucine','Lysine','Methionine','Phenylalanine','Valine','Histidine']
ESSENTIAL_AMINO_ACIDS_REGEX = '|'.join(ESSENTIAL_AMINO_ACIDS)

def format_ds(df):
    return df.loc[:, USEFUL_COLUMNS]

@click.group()
def cli():
    pass

@cli.command()
@click.option('--food-name', prompt='The name of the food to search for')
def search(food_name):
    terms = food_name.strip().split()
    filtered_data = None

    if len(terms) == 0:
        raise Exception('Received an empty string, was looking for a food name.')
    elif len(terms) == 1:
        filtered_data = NUTRIENT_DATASET.loc[NUTRIENT_DATASET['Shrt_Desc'].str.contains(terms[0], case=False)]
    else:
        filtered_data = NUTRIENT_DATASET.loc[
            functools.reduce(
                lambda a, b: NUTRIENT_DATASET['Shrt_Desc'].str.contains(a, case=False) & \
                        NUTRIENT_DATASET['Shrt_Desc'].str.contains(b, case=False),
                terms
            )
        ]

    amino_acid_info = filtered_data.loc[filtered_data[NUTRIENT_DESC_COLUMN].str.contains(ESSENTIAL_AMINO_ACIDS_REGEX, case=False)]
    click.echo(format_ds(amino_acid_info))

cli.add_command(search)

if __name__ == '__main__':

    global NUTRIENT_DATASET
    NUTRIENT_DATASET = pd.read_csv(f'{NUTRIENT_CSV_DIR}/csv/merged_data.csv', low_memory=False)

    cli()

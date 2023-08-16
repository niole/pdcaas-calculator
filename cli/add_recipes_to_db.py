"""
this adds the recipes in the json files that are output by the cli.py to the sqlite3 food.db
"""

from sqlalchemy.orm import Session
from engine import engine, Recipe, IngredientAminoAcid, Ingredient, RecipeAminoAcid
import click
import json

def create_recipe_aa_models(summary):
    def get_aa_from_summary(name, key):
        try:
            return RecipeAminoAcid(
                name=name,
                g=summary[key]
            )
        except Exception as e:
            print(f"Failed to get aa from summary: {e}")
            return None

    return [aa for aa in [
            get_aa_from_summary("Tryptophan", "digestible_eaa_Tryptophan_g"),
            get_aa_from_summary("Histidine", "digestible_eaa_Histidine_g"),
            get_aa_from_summary("Valine", "digestible_eaa_Valine_g"),
            get_aa_from_summary("Phenylalanine", "digestible_eaa_Phenylalanine_g"),
            get_aa_from_summary("Methionine", "digestible_eaa_Methionine_g"),
            get_aa_from_summary("Lysine", "digestible_eaa_Lysine_g"),
            get_aa_from_summary("Leucine", "digestible_eaa_Leucine_g"),
            get_aa_from_summary("Isoleucine", "digestible_eaa_Isoleucine_g"),
            get_aa_from_summary("Threonine", "digestible_eaa_Threonine_g"),
    ] if aa is not None]

def create_ingredient_aa_model(aa):
    return IngredientAminoAcid(
        name=aa["name"],
        g=aa["total_protein_g"]
    )


def create_ingredient_model(ingredient, ingredient_summary):
    return Ingredient(
        name=ingredient["name"],
        unit=ingredient["unit"],
        amount=ingredient["amount"],
        digestible_protein_g=ingredient_summary["total_achievable_protein_food_g"],
        total_protein_g=ingredient_summary["total_protein_g"],
        td=ingredient_summary["td"],
        aas=[create_ingredient_aa_model(aa) for aa in ingredient_summary["aas"]]
    )


def create_models(recipe):
    nutrient_summary = recipe["nutrient_breakdown"]["protein_breakdown"]
    ingredients = [create_ingredient_model(i, i_summary) for (i_summary, i) in zip(nutrient_summary["ingredient_summaries"], recipe["ingredients"])]
    aas = create_recipe_aa_models(nutrient_summary)
    rmodel = Recipe(
         title=recipe['title'],
         total_protein_g=nutrient_summary["total_protein_g"],
         total_eaa_g=nutrient_summary["total_eaa_g"],
         total_complete_digestible_protein_g=nutrient_summary["total_complete_digestible_protein_g"],
         limiting_aa=nutrient_summary["limiting_amino_acid_name"],
         ingredients=ingredients,
         aas=aas,
     )

    return [rmodel]

@click.command()
@click.option('--inpaths', '-i', multiple=True)
def main(inpaths):
    with Session(engine) as session:
        for path in inpaths:
            with open(path, 'r') as file:
                recipes = json.loads(file.read())
                for recipe in recipes:
                    ms = create_models(recipe)
                    session.add_all(ms)

            session.commit()

if __name__ == "__main__":
    main()

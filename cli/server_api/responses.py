from pydantic import BaseModel

def to_recipes_json(found_recipes: list[list[dict]]):
    response = []
    for recipes in found_recipes:
        json_recipes = []
        for r in recipes:
            result = {
                'id': r['id'],
            }

            result.update(r['metadata'])

            json_recipes.append(result)

        response.append(json_recipes)

    return response

class RecipeNutritionSummary(BaseModel):
    id: str
    total_complete_digestible_protein_g: float
    total_protein_g: float
    total_eaa_g: float
    limiting_amino_acid_name: str
    limiting_amino_acid_g: float
    digestible_eaa_Tryptophan_g: float | None
    digestible_eaa_Threonine_g: float | None
    digestible_eaa_Isoleucine_g: float | None
    digestible_eaa_Leucine_g: float | None
    digestible_eaa_Lysine_g: float | None
    digestible_eaa_Methionine_g: float | None
    digestible_eaa_Phenylalanine_g: float | None
    digestible_eaa_Valine_g: float | None
    digestible_eaa_Histidine_g: float | None


class RecipeMatchesResponse(BaseModel):
    data: list[tuple[str, list[RecipeNutritionSummary]]]

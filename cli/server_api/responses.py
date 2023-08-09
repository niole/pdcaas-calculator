from pydantic import BaseModel

def to_recipes_json(found_recipes: list[list[dict]]):
    response = []
    for recipes in found_recipes:
        json_recipes = []
        for r in recipes:
            json_recipes.append({
                'id': r['id'],
                'percent_complete_digestible_protein': r['metadata']['percent_complete_digestible_protein'],
                'total_complete_digestible_protein_g': r['metadata']['total_complete_digestible_protein_g'],
                'total_protein_g': r['metadata']['total_protein_g'],
            })
        response.append(json_recipes)

    return response

class RecipeNutritionSummary(BaseModel):
    id: str
    percent_complete_digestible_protein: float
    total_complete_digestible_protein_g: float
    total_protein_g: float

class RecipeMatchesResponse(BaseModel):
    data: list[tuple[str, list[RecipeNutritionSummary]]]

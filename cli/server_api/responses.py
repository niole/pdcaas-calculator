from pydantic import BaseModel
from typing import List, Optional

class IngredientAminoAcidResponse(BaseModel):
    id: int
    ingredient_id: int
    name: str
    g: float

class IngredientResponse(BaseModel):
    id: int
    recipe_id: int
    name: str
    unit: str
    amount: float
    digestible_protein_g: Optional[float]
    total_protein_g: Optional[float]
    td: Optional[float]
    aas: List[IngredientAminoAcidResponse]

def to_ingredient_aa_response(aa: dict) -> IngredientAminoAcidResponse:
    return IngredientAminoAcidResponse(
        id=aa.id,
        ingredient_id=aa.ingredient_id,
        name=aa.name,
        g=aa.g
    )

def to_ingredient_response(i: dict) -> IngredientResponse:
    return IngredientResponse(
        id=i.id,
        recipe_id=i.recipe_id,
        name=i.name,
        unit=i.unit,
        amount=i.amount,
        digestible_protein_g=i.digestible_protein_g,
        total_protein_g=i.total_protein_g,
        td=i.td,
        aas=[to_ingredient_aa_response(aa) for aa in i.aas]
    )

def to_recipes_json(found_recipes: list[list[dict]]) -> list[dict]:
    response = []
    ids = []
    for recipes in found_recipes:
        for r in recipes:
            if r['score'] >= 0.7 and r['id'] not in ids:
                result = {
                    'id': r['id'],
                }

                result.update(r['metadata'])

                response.append(result)
                ids.append(r['id'])
    return response

class RecipeAminoAcidResponse(BaseModel):
    id: int
    recipe_id: int
    name: str
    g: float

def to_recipe_aa_response(aa: dict) -> RecipeAminoAcidResponse:
    return RecipeAminoAcidResponse(
        id=aa.id,
        recipe_id=aa.recipe_id,
        name=aa.name,
        g=aa.g
    )

class RecipeResponse(BaseModel):
    id: int
    title: str
    total_protein_g: Optional[float]
    total_eaa_g: Optional[float]
    total_complete_digestible_protein_g: Optional[float]
    limiting_aa: Optional[str]
    instructions: str
    ingredients: List[IngredientResponse]
    aas: List[RecipeAminoAcidResponse]

def to_recipe_response(r: dict) -> RecipeResponse:
    return RecipeResponse(
        id=r.id,
        title=r.title,
        total_protein_g=r.total_protein_g,
        total_eaa_g=r.total_eaa_g,
        total_complete_digestible_protein_g=r.total_complete_digestible_protein_g,
        limiting_aa=r.limiting_aa,
        instructions=r.instructions,
        ingredients=[to_ingredient_response(i) for i in r.ingredients],
        aas=[to_recipe_aa_response(aa) for aa in r.aas]
    )

"""
The recipe with all details, ingredients and nutritional information
"""
class RecipeListResponse(BaseModel):
    data: List[RecipeResponse]

"""
A summary of a recipe and it's nutritional value
"""
class RecipeNutritionSummary(BaseModel):
    id: str
    total_complete_digestible_protein_g: float | None
    total_protein_g: float | None
    total_eaa_g: float | None
    limiting_amino_acid_name: str | None
    limiting_amino_acid_g: float | None
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
    data: list[RecipeNutritionSummary]

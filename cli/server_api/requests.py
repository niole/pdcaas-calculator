from pydantic import BaseModel

"""
specifies recipe names to find the closest match for
"""
class RecipeMatchesRequest(BaseModel):
    recipe_names: list[str]

"""
specifies recipe names to find exact matches for 
"""
class GetRecipesRequest(BaseModel):
    recipe_names: list[str]

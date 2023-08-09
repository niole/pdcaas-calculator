from pydantic import BaseModel

class RecipeMatchesRequest(BaseModel):
    recipe_names: list[str]


"""
The recipe server provides an API for getting recipes, either directly or the best match.
"""
from fastapi import FastAPI
import json
from pinecone_client import find_limit_vector_query
from sentence_transformers import SentenceTransformer
from server_api.requests import *
from server_api.responses import *
from engine import *
from sqlalchemy import select
from sqlalchemy.orm import Session

model = SentenceTransformer('./transformers/vegan_improved_food_item_transformer')

app = FastAPI()

@app.route("/")
def health_check():
    return "hello"

"""
returns 1 recipe for each recipe name provided
"""
@app.post("/recipe/matches", response_model=RecipeMatchesResponse)
def recipe_matches_metadata(body: RecipeMatchesRequest):
    recipe_names = body.recipe_names
    found_recipes = [find_limit_vector_query(name, 1, 'recipes', providedModel=model, include_values=False) for name in recipe_names]

    response =  to_recipes_json(found_recipes)
    return { 'data': response }

"""
gets the recipes according to a filter
"""
@app.post("/recipe/list", response_model=RecipeListResponse)
def recipe_list(body: GetRecipesRequest):
    ids = body.ids

    with Session(engine) as session:
        stmt = select(Recipe).where(Recipe.id.in_(ids))
        result = session.execute(stmt)
        data = [to_recipe_response(o) for o in result.scalars()]
        return { 'data': data }
    return { 'data': [] }

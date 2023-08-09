"""
The recipe server provides an API for getting recipes, either directly or the best match.
"""
from fastapi import FastAPI
import json
from pinecone_client import find_limit_vector_query
from sentence_transformers import SentenceTransformer
from server_api.requests import *
from server_api.responses import to_recipes_json, RecipeMatchesResponse

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

    response =  list(zip(recipe_names, to_recipes_json(found_recipes)))
    return { 'data': response }

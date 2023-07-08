import os
import re
import hashlib
import openai
import logging
import json
from fractions import Fraction
from functools import partial
import multiprocessing
from multiprocessing import Pool
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig()
logging.root.setLevel(logging.INFO)

logger = multiprocessing.get_logger()
logger.setLevel(logging.INFO)

OH_SHE_GLOWS_ORIGIN = 'ohsheglows'
BAREFOOT_CONTESSA_ORIGIN = 'barefootcontessa'

#openai.organization = "Personal"
openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_json(s):
    try:
        return json.loads(s)
    except Exception as e:
        logger.error(f"Failed to parse string as json: {e}")
        return None

def build_prompt(ingredients_json):
    prompt = f"rewrite the following JSON to fix the schema. \n JSON: {ingredients_json}" + '\n SCHEMA: [{"units": "cup", "name": "wheat pasta", "total": 1}, {"units":"tsp", "name":"salt","total": 0.5}, {"units": "lbs", "name": "beef", "total": 1}, {"units": "teaspoon", "name": "mustard", "total": 0.25}, {"units": "tablespoon", "name":"peanut butter" , "total": 2}, {"units":"tbsp", "name":"sour cream", "total":1.5}]'

    return prompt

def remove_all_leading_chars(s):
    p = r'^.*?\['
    return re.sub(p, '[', s)

def remove_all_trailing_chars(s):
    p = r'\][\s\w]*$'
    return re.sub(p, ']', s)

def remove_newlines(s):
    return s.replace("\n", "")

def replace_ranges(s):
    p1 = r'\d+\.?\d*\s*-\s*(\d+\.?\d*)'
    p2 = r'\d+\.?\d*\s*to\s*(\d+\.?\d*)'

    for match in re.finditer(p1, s):
        replacement = match.groups()[0]
        s = re.sub(match[0], replacement, s)

    for match in re.finditer(p2, s):
        replacement = match.groups()[0]
        s = re.sub(match[0], replacement, s)

    return s

"""
parses out the ingredient quanitites from the scraped recipe json string
cleans the string and then tries to parse it as json
s - stringified json recipe to parse
output_details - (origin label string, output file path)
"""
def parse_ingredient_units(s, output_details, mock_api = False):
    cleaned_s = remove_newlines(s)

    parsed_recipe = parse_json(cleaned_s)
    if parsed_recipe is not None: 
        title = parsed_recipe["title"]
        logger.warning(f'Parsing {title}')

        ingredients = parsed_recipe['ingredients']
        prompt = build_prompt(ingredients)

        try:
            ingredients_w_units = []

            if not mock_api:
                res = openai.Completion.create(
                  model="text-davinci-003",
                  prompt=prompt,
                  max_tokens=2000,
                  temperature=1
                )
                raw_response = res['choices'][0]['text']
                ingredients_w_units = parse_ingredients_json_response(raw_response)

                if ingredients_w_units is None:
                    raise Exception("Failed to parse recipe json")

            write_recipe_to_file(parsed_recipe, ingredients_w_units, output_details)
        except Exception as e:
            logger.error(f'Failed to extract response for {title}: {e}')
            logger.error(f'Failed input for {title}: {ingredients}')
            logger.error(f'Failed response for {title}: {res}')
    else:
        logger.error(f'Couldn\'t parse recipe into json.')
    return None

def replace_fractions(s):
    p = r'\d+\/\d+'
    for match in re.finditer(p, s):
        m = match.group()
        s = s.replace(m, str(float(Fraction(m))))
    return s

def parse_ingredients_json_response(raw_response):
    cleaned_response = replace_ranges(replace_fractions(remove_all_trailing_chars(remove_all_leading_chars(remove_newlines(raw_response)))))
    return parse_json(cleaned_response)

def write_recipe_to_file(recipe, ingredients_w_units, output_details):
    (origin, output_filepath) = output_details
    recipe['id'] = hashlib.md5((origin + recipe['title']).encode()).hexdigest()
    recipe['ingredients_w_units'] = ingredients_w_units

    s = json.dumps(recipe)
    with open(output_filepath, 'a') as file:
        file.write(s)

"""
This parses the ingredients from inside files of raw recipe data using open ai so that each ingredient has units, amounts, and names
in a JSON format.
{ title: string, ingredients: string[] } -> { title: string, id: string, ingredients: string[], ingredients_w_units: { name: string, units: string, total: number }[] }

the input JSON files have a JSON blob on each line
the output JSON files have JSON blobs outputted onto 1 line, with no comma separation
"""
def parse_jsonl(origin, filepath, output_filepath, max_recipes = None):
    with open(filepath, "r") as file:
        lines = file.readlines()
        if max_recipes is not None:
            lines = lines[:max_recipes]

        with Pool(10) as p:
            # some lines will fail to be parsed and be None
            p.map(partial(parse_ingredient_units, output_details=(origin, output_filepath)), lines)

def test_parse_ingredient_units():
    s = "SCHEMA CORRECTED \n\n{\"title\":\"sdfsdf\", \"ingredients\":[{\"units\":\"cup\", \"name\":\"sweet onion, chopped\", \"total\": 2},{\"units\":\"cup\", \"name\":\"vegetable broth\", \"total\": 5-6.5}, {\"units\":\"cup\", \"name\":\"dry red lentils\", \"total\": 0.5},  {\"units\":\"cup\", \"name\":\"dry green/brown lentils\", \"total\": 1}, {\"units\":\"tsp\", \"name\":\"Kosher salt & pepper\", \"total\": 0.5}]} trialing chars"

    parse_ingredient_units(s, ('thebarefootcontessa', 'test_out.txt'), True)
    parse_ingredient_units(s, ('thebarefootcontessa', 'test_out.txt'), True)

def test_parse_ingredients_json_response():
    raw_response = "\n\n[{\"units\": \"cup\", \"name\": \"vegan fractions 2 \", \"total\": 10/2}, {\"units\": \"cup\", \"name\": \"vegan fractions \", \"total\": 1/2}, {\"units\": \"cup\", \"name\": \"vegan butter\", \"total\": 0.5}, {\"units\":\"tsp\", \"name\":\"pumpkin pie spice\",\"total\": 2-3}, {\"units\": \"teaspoon\", \"name\": \"vanilla extract\", \"total\": 1}, {\"units\": \"pinch\", \"name\": \"sea salt or pink salt\", \"total\": 1-1.5}, {\"units\": \"cups\", \"name\":\"powdered icing sugar more space english\" , \"total\": 2.6  to 3},  {\"units\": \"cups\", \"name\":\"powdered icing sugar more space dash\" , \"total\": 2  - 3}, {\"units\": \"cups\", \"name\":\"powdered icing sugar\" , \"total\": 2-3}, {\"units\":\"tbsp\", \"name\":\"non-dairy milk\", \"total\": 0.5-1}] end response"

    expected = [{'units': 'cup', 'name': 'vegan fractions 2 ', 'total': 5.0}, {'units': 'cup', 'name': 'vegan fractions ', 'total': 0.5}, {'units': 'cup', 'name': 'vegan butter', 'total': 0.5}, {'units': 'tsp', 'name': 'pumpkin pie spice', 'total': 3}, {'units': 'teaspoon', 'name': 'vanilla extract', 'total': 1}, {'units': 'pinch', 'name': 'sea salt or pink salt', 'total': 1.5}, {'units': 'cups', 'name': 'powdered icing sugar more space english', 'total': 3}, {'units': 'cups', 'name': 'powdered icing sugar more space dash', 'total': 3}, {'units': 'cups', 'name': 'powdered icing sugar', 'total': 3}, {'units': 'tbsp', 'name': 'non-dairy milk', 'total': 1}]
    p = parse_ingredients_json_response(raw_response)

    assert(p == expected)


#if __name__ == "__main__":
#    test_parse_ingredient_units()
#    test_parse_ingredients_json_response()


if __name__ == "__main__":
    #parse_jsonl(OH_SHE_GLOWS_ORIGIN, 'scrapes/data/ohsheglows.jsonl', 'open_ai/data/ohsheglows.json')
    #parse_jsonl(BAREFOOT_CONTESSA_ORIGIN, 'scrapes/data/barefootcontessa.jsonl', 'open_ai/data/barefootcontessa.json')
    pass

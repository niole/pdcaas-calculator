# About

This project contains a web application for recommending meals with complete protein profiles.
- `nutrition-assistant` is the web app.
- `cli` contains functionality for ingesting and imbedding in vectors and adding to a pinecode vector db parsed recipe data and nutritional information from the nutritional information database mentioned below.
- `scrapes` contains methods for attaining recipe data.
- `open_ai` contains utilities for parsing ingredient names, units, and amounts out of the recipe data which is then processed by the utilities in `cli`


# Nutritional Information Database
The data used in the `food_info_types`, `td_types` and `weights` tables were derived from the 2019 [usda national nutrient database standard reference legacy release](https://data.nal.usda.gov/dataset/usda-national-nutrient-database-standard-reference-legacy-release).

The database containing these tables is a sqlite3 called `food.db`, which is not in this repo.

This repo also contains an [explanatory pdf](Calculating-PDCAAS-for-Percent-Protein-Slide-Deck.pdf), which explains PDCAAS scoring and its significance.

# Setup

```sh
cd cli
python3 -m venv "venv"
. venv/bin/activate
pip install -r requirements.txt

# unzip the database
unzip fooddb.zip

# create a .env file
PINECONE_API_KEY=...
OPENAI_API_KEY=...
RECIPE_MATCH_API_SERVER_DOMAIN="http://127.0.0.1:8000"

# download and put the following transformers into the transformers directory
cli/transformers/vegan_improved_food_item_transformer
cli/transformers/food_item_transformer/

# install the dependencies in the nutritional nutrition-assistant
npm i
```

# Update the vector database

Populate the vector db namespaces by running the following commands in order:
```sh
python create_food_info_vector_tables.py --model_path transformers/vegan_improved_food_item_transformer --embed_weights
python create_food_info_vector_tables.py --model_path transformers/vegan_improved_food_item_transformer --embed_td
python create_food_info_vector_tables.py --model_path transformers/vegan_improved_food_item_transformer --embed_food_items
```

# Generate recipes with nutritional information
```sh
# may take a while
python cli.py -i <scraped recipe data array json> -o open_ai/data
```

# Update recipes namespace with vectors from recipes with nutritional data
```sh
python create_food_info_vector_tables.py --model_path transformers/vegan_improved_food_item_transformer --embed_recipes --recipe_paths open_ai/data/<recipe with nutrition info>
```

# Run the recipe server
```sh
uvicorn server:app --reload
```

# Add recipes to food.db, the sqlite3 db 
```sh
python add_recipes_to_db.py -i recipes_1.json -i recipes_2.json
```

# Sources
If you want to work with the csv data, unzip sources.zip into the sources/ directory

# How-To

## add nutrient data to scraped recipes

```sh
SCRAPED_DATA=scrapes/data/ohsheglows.jsonl

python open_ai/parse_ingredients.py -i vegan $SCRAPED_DATA -o 'open_ai/test_data'

cat open_ai/test_data/ohsheglows.json | jq -sc '.' > open_ai/test_data/ohsheglows_array.json

python cli.py -i open_ai/test_data/ohsheglows_array.json -o open_ai/test_data

cat open_ai/test_data/ohsheglows_array_w_nutrients.json | jq 'length'
```

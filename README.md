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
```

# API Examples

```sh
python cli.py
```

# Munge data

```sh
./create_all_csvs.sh
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

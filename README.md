# About

The data used in this tool was derived from the [usda national nutrient database standard reference legacy release](https://data.nal.usda.gov/dataset/usda-national-nutrient-database-standard-reference-legacy-release).

# Setup

```sh
pipenv install

export NUTRIENT_CSV_DIR=/tmp
unzip merged_csv -d $NUTRIENT_CSV_DIR
```

# API Examples

## Help

```sh
pipenv run python search.py --help
```

## Get amino acid information for a food

```sh
pipenv run python search.py --food-name "soft tofu"
```

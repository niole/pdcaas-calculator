# Setup

```sh
pipenv install

export NUTRIENT_CSV_DIR=/tmp
unzip merged_csv -d $NUTRIENT_CSV_DIR
```

# Get amino acid information for a food

```sh
pipenv run python search.py --food-name "soft tofu"
```

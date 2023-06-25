# About

The data used in this tool was derived from the 2019 [usda national nutrient database standard reference legacy release](https://data.nal.usda.gov/dataset/usda-national-nutrient-database-standard-reference-legacy-release).

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

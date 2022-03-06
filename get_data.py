import pandas as pd

def main():
    return pd.read_csv('./csv/merged_data.csv',  low_memory=False)

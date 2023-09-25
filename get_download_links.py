import requests
import pandas as pd
import sys
import yaml

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

y = sys.argv[1]
m = sys.argv[2].zfill(2)

if __name__ == "__main__":
    
    # Get all of the files in our date range
    df = pd.DataFrame()
    link = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=contains(Name,'S5P_') and contains(Name,'__CH4___') and ContentDate/Start gt {y}-{m}-01T00:00:00.000Z and ContentDate/Start lt {y}-{str(int(m)+1).zfill(2)}-01T00:00:00.000Z"
    while True:

        print(link)
        json = requests.get(link).json()

        if len(df) == 0:
            df = pd.DataFrame.from_dict(json['value'])
        else:
            df = pd.concat([df,pd.DataFrame.from_dict(json['value'])], ignore_index=True)

        if '@odata.nextLink' in json.keys():
            link = json['@odata.nextLink']
        else:
            break

    # Add processor version, processor mode, and orbit number
    df["ProcessorVersion"] = df["Name"].str.extract(r'_(\d{6})_')
    df["ProcessingMode"] = df["Name"].str.extract(r'_(\S{4})_')
    df["OrbitNumber"] = df["Name"].str.extract(r'_(\d{5})_')

    # Drop non-02.04.00/02.05.00 processor versions
    df = df.drop(df[~((df["ProcessorVersion"] == "020400") | (df["ProcessorVersion"] == "020500"))].index).reset_index(drop=True)

    # Drop OFFL if orbit number is less than 24780
    # Follows recommendation here: https://sentinels.copernicus.eu/documents/247904/3541451/Sentinel-5P-Methane-Product-Readme-File
    df = df.drop(df[(df["OrbitNumber"].astype(int) < 24780) & (df["ProcessingMode"] == "OFFL")].index).reset_index(drop=True)

    # Make sure there are no repeats
    assert len(df["OrbitNumber"].unique()) == len(df)

    # Write to links.txt
    for idx in df.index:
        url = f"http://catalogue.dataspace.copernicus.eu/odata/v1/Products({df.loc[idx,'Id']})/$value\n"
        with open("links.txt", "a") as f:
            f.write(url)
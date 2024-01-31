import requests
import pandas as pd
import sys
import yaml
import time

y = sys.argv[1]
m = sys.argv[2].zfill(2)

if __name__ == "__main__":
    
    # Get all of the files in our date range
    df = pd.DataFrame()
    start = f"{y}-{m}"
    if m == "12":
        end = f"{int(y)+1}-01"
    else:
        end = f"{y}-{str(int(m)+1).zfill(2)}"
    link = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=contains(Name,'S5P_') and contains(Name,'__CH4___') and ContentDate/Start gt {start}-01T00:00:00.000Z and ContentDate/Start lt {end}-01T00:00:00.000Z"
    while True:

        print(link)
        json = requests.get(link).json()
        time.sleep(1)

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
    df["CollectionNumber"] = df["Name"].str.extract(r'_(\d{2})_')

    # Drop non-02.04.00/02.05.00 processor versions
    df = df.drop(df[~((df["ProcessorVersion"] == "020400") | (df["ProcessorVersion"] == "020500"))].index).reset_index(drop=True)

    # Drop non-collection 03 (accounts for odd collection 93 files in 2018-09)
    df = df.drop(df[df["CollectionNumber"] != "03"].index).reset_index(drop=True)

    # If RPRO and OFFL exist, choose RPRO (it was reprocessed for a reason!)
    # Follows recommendation here: https://sentinels.copernicus.eu/documents/247904/3541451/Sentinel-5P-Methane-Product-Readme-File
    unique_orbit_numbers = df["OrbitNumber"].unique()
    for unique_orbit_number in unique_orbit_numbers:
        subset = df.loc[df["OrbitNumber"] == unique_orbit_number]
        if len(subset) == 1:
            continue
        else:
            index_of_files_to_keep = subset.loc[subset["ProcessingMode"] == "RPRO"].index
            assert len(index_of_files_to_keep) == 1
            index_of_files_to_drop = subset.loc[subset["ProcessingMode"] != "RPRO"].index
            print(index_of_files_to_drop)
            df = df.drop(index_of_files_to_drop)

    # Make sure there are no repeats
    assert len(df["OrbitNumber"].unique()) == len(df)

    # Write to links.txt
    for idx in df.index:
        url = f"http://catalogue.dataspace.copernicus.eu/odata/v1/Products({df.loc[idx,'Id']})/$value\n"
        with open("links.txt", "a") as f:
            f.write(url)
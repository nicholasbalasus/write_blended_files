# This script downloads the TROPOMI CH4 files from the Copernicus Data Space
# Ecosystem for one month. It handles determing which files to download
# following the recommendations in the TROPOMI CH4 ReadMe.

import requests
import pandas as pd
import multiprocessing
import boto3
import os
import sys
sys.dont_write_bytecode = True
from config import dir,date

# Function to initialize for S3
s3 = None
def initialize():
    global s3
    credentials = boto3.Session().get_credentials()
    endpoint_url = "https://eodata.dataspace.copernicus.eu"
    s3 = boto3.client('s3', aws_access_key_id=credentials.access_key,
                    aws_secret_access_key=credentials.secret_key,
                    endpoint_url=endpoint_url)

if __name__ == "__main__":

    start_date = f"{date}-01"
    end_date = ((pd.to_datetime(start_date) + pd.DateOffset(months=1))
                .strftime("%Y-%m-%d"))

    # Account for partial month
    if start_date == "2018-04-01":
        start_date = "2018-04-30"

    # Make a directory to save the files to
    dir = dir + "/" + date + "/" + "tropomi"
    os.makedirs(dir, exist_ok=True)

    # Use S3 to get a list of all possible CH4 files in our time range. This
    # will include many files with outdated processors that we will filter out.
    years, months, days = [], [], []
    current_date = pd.to_datetime(start_date)
    while current_date != pd.to_datetime(end_date):
        years.append(current_date.strftime("%Y"))
        months.append(current_date.strftime("%m"))
        days.append(current_date.strftime("%d"))
        current_date += pd.Timedelta(days=1)

    # Get access to S3
    initialize()

    # Collect information about each of the files
    names = []
    prefixes = []
    for i in range(len(days)):
        Prefix=(f"Sentinel-5P/TROPOMI/L2__CH4___/"
                f"{years[i]}/{months[i]}/{days[i]}/")
        for key in s3.list_objects(Bucket="eodata", Prefix=Prefix)["Contents"]:
            prefixes.append(Prefix)
            names.append(key["Key"].split("/")[-2])

    # Organize the information about each of the files
    df = pd.DataFrame()
    df["Name"] = names
    df["Prefix"] = prefixes
    df["ProcessorVersion"] = df["Name"].str.extract(r'_(\d{6})_')
    df["ProcessingMode"] = df["Name"].str.extract(r'_(\S{4})_')
    df["OrbitNumber"] = df["Name"].str.extract(r'_(\d{5})_')
    df["ModificationDate"] = df["Name"].str.extract(r'_\d{6}_(\d{8}T\d{6})')
    df["CollectionNumber"] = df["Name"].str.extract(r'_(\d{2})_')

    # We only want files that are v02.04.00, v02.05.00, or v02.06.00.
    # Also make sure the collection number is 03 to account for some duplicates.
    df = df.loc[((df["ProcessorVersion"] == "020400") |
                (df["ProcessorVersion"] == "020500") |
                (df["ProcessorVersion"] == "020600"))]
    df = df.drop_duplicates(subset=["Name","ModificationDate"])
    df = df.loc[df["CollectionNumber"] == "03"].reset_index(drop=True)

    # Deal with duplicate orbit numbers.
    unique_orbit_numbers = df["OrbitNumber"].unique()
    for unique_orbit_number in unique_orbit_numbers:
        subset = df.loc[df["OrbitNumber"] == unique_orbit_number]
        # If this ids already a unique orbit, continue.
        if len(subset) == 1:
            continue
        # If there is both RPRO and OFFL, keep RPRO.
        elif len(subset["ProcessingMode"].unique()) > 1: 
            index_to_drop = subset.loc[subset["ProcessingMode"] != "RPRO"].index
            df = df.drop(index_to_drop)

    assert len(df) == len(df["OrbitNumber"].unique())
    df = df.reset_index(drop=True)
    df["S3Path"] = df["Prefix"] + df["Name"]
    s3_paths = sorted(df["S3Path"].to_list())
    print(f"Going to download {len(s3_paths)} files.")

    # Follow stack overflow directions to download over multiple cores.
    # Copernicus specifies that the maxnumber of concurrent connections is 4.
    def download_from_s3(s3_path):
        bucket_name = "eodata"
        file =  s3_path.split("/")[-1] + ".nc"
        object_key = s3_path + "/" + file
        local_file_path = dir + "/" + file
        s3.download_file(bucket_name, object_key, local_file_path)

    with multiprocessing.Pool(4, initialize) as pool:
        pool.map(download_from_s3, s3_paths)
        pool.close()
        pool.join()  
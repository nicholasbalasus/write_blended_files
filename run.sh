#!/bin/bash

#SBATCH -t 2-00:00
#SBATCH -c 40
#SBATCH --mem 96000
#SBATCH -p huce_cascade,seas_compute

# Setup
source ~/.bashrc
source utils.sh
eval $(parse_yaml config.yml)
username=$( awk -v machine="identity.dataspace.copernicus.eu" '$2 == machine {print $4 }' ~/.netrc )
password=$( awk -v machine="identity.dataspace.copernicus.eu" '$2 == machine {print $6 }' ~/.netrc )
export ACCESS_TOKEN=$(curl -d 'client_id=cdse-public' \
                    -d "username=${username}" \
                    -d "password=${password}" \
                    -d 'grant_type=password' \
                    'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' | \
                    python3 -m json.tool | grep "access_token" | awk -F\" '{print $4}')

# Get the uncompressed model_lgbm.pkl file
gunzip -k model_lgbm.pkl.gz

# Loop through the array of Months
read -a Months <<< "$Months" # converts Months to an array
for Month in "${Months[@]}"; do

  # Download the TROPOMI data for the given month and year
  download_tropomi $Year $Month

  # Write the Blended data for the given month and year
  write_blended $Year $Month

done

# Remove the uncompressed model_lgbm.pkl file
rm model_lgbm.pkl
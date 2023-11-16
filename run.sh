#!/bin/bash

#SBATCH -t 5-00:00
#SBATCH -c 48
#SBATCH --mem 96000
#SBATCH -p seas_compute

# Function to parse yaml files from Stefan Farestam (https://stackoverflow.com/questions/5014632/how-can-i-parse-a-yaml-file-from-a-linux-shell-script)
parse_yaml() {
  local prefix=$2
  local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
  sed -ne "s|^\($s\):|\1|" \
      -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
      -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
  awk -F$fs '{
    indent = length($1)/2;
    vname[indent] = $2;
    for (i in vname) {if (i > indent) {delete vname[i]}}
    if (length($3) > 0) {
      vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
      printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
    }
  }'
}

# Function that downloads TROPOMI data for a given month and year and then writes the corresponding blended files
download_tropomi_and_write_blended () {
  # setup
  Month=$1
  cwd="$(pwd)"
  dir="${StorageDir}/${Year}-$(printf "%02d" $Month)/tropomi"
  mkdir -p "${dir}"
  cd "${dir}/.."

  # form a list of urls to download
  touch links.txt
  source ~/.bashrc
  conda activate blnd_env
  python "${cwd}/get_download_links.py" $Year $Month

  # download tropomi data with wget
  username=$( awk -v machine="identity.dataspace.copernicus.eu" '$2 == machine {print $4 }' ~/.netrc )
  password=$( awk -v machine="identity.dataspace.copernicus.eu" '$2 == machine {print $6 }' ~/.netrc )
  split -l 5 links.txt links_ # split into multiple files to allow us to periodically regenerate the ACCESS_TOKEN
  for file in links_*; do
    export ACCESS_TOKEN=$(curl -d 'client_id=cdse-public' \
                      -d "username=${username}" \
                      -d "password=${password}" \
                      -d 'grant_type=password' \
                      'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token' | \
                      python3 -m json.tool | grep "access_token" | awk -F\" '{print $4}')
    xargs -n 1 -P 4 wget -nv --retry-connrefused --tries=0 --content-disposition --header "Authorization: Bearer $ACCESS_TOKEN" -P "${dir}" < $file
    wait
  done

  # extract the .nc files
  cd "${dir}"
  find . -name "*.zip" | xargs -P 40 -I {} sh -c 'unzip -q -j "{}" "*.nc" && rm "{}"'
  cd "${dir}/.."

  # write blended files
  mkdir -p "${StorageDir}/${Year}-$(printf "%02d" $Month)/blended"
  python "${cwd}/write_blended_files.py" $cwd $Year $Month

  # cleanup
  rm links*
  cd "${cwd}"
}

# Setup
eval $(parse_yaml config.yml)
gunzip -k "model_lgbm.pkl.gz"

# Loop through the array of Months
read -a Months <<< "$Months" # converts Months to an array
for Month in "${Months[@]}"; do

  # Download the TROPOMI data and write the Blended data for the given month
  download_tropomi_and_write_blended $Month

done

# Cleanup
rm model_lgbm.pkl

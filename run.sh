#!/bin/bash

#SBATCH -t 5-00:00
#SBATCH -c 48
#SBATCH --mem 96000
#SBATCH -p seas_compute

# Function to parse yaml files from Stack Overflow
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

# Function that downloads TROPOMI data for a month/year and 
# then writes the corresponding blended files
download_tropomi_and_write_blended () {

  # Setup
  Month=$1
  dir="${StorageDir}/${Year}-$(printf "%02d" $Month)/tropomi"
  mkdir -p "${dir}"
  mkdir -p "${StorageDir}/${Year}-$(printf "%02d" $Month)/blended"

  # Form a list of urls to download
  source ~/.bashrc
  conda activate blnd_env
  python "get_download_links.py" $Year $Month

  # Download tropomi data with wget
  while read link; do
    wget -nv --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies --content-disposition --tries=5 -P ${dir} ${link}
  done < links.txt

  # Write blended files
  python "write_blended_files.py" $Year $Month

  # Cleanup
  rm links.txt

}

# Setup
eval $(parse_yaml config.yml)
gunzip -k "model_lgbm.pkl.gz"

# Loop through the array of Months
read -a Months <<< "$Months"
for Month in "${Months[@]}"; do
  download_tropomi_and_write_blended $Month
done

# Cleanup
rm model_lgbm.pkl

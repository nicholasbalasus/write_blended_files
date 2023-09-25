#!/bin/bash

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

# Function that downloads TROPOMI data for a given month and year
download_tropomi () {
    Year=$1
    Month=$2
    cwd="$(pwd)"
    dir="${StorageDir}/tropomi/${Year}-$(printf "%02d" $Month)"
    mkdir -p "${dir}"

    # form a list of urls to download
    touch links.txt
    conda activate blnd_env
    python get_download_links.py $Year $Month

    # download tropomi data with wget
    xargs -n 1 -P 40 wget -q --content-disposition --header "Authorization: Bearer $ACCESS_TOKEN" -P "${dir}" < links.txt

    # remove text files
    rm links.txt

    # Extract the .nc files
    cd "${dir}"
    find . -name "*.zip" | xargs -P 40 -I {} sh -c 'unzip -q -j "{}" "*.nc" && rm "{}"'
    cd "${cwd}"
}

write_blended () {
    Year=$1
    Month=$2
    mkdir -p ${StorageDir}/blended/${Year}-$(printf "%02d" $Month)
    conda activate blnd_env
    python write_blended_files.py $Year $Month
}
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

# Utility function for download_tropomi
append_output_txt_to_files_txt () {
    grep "link href=\"https" output.txt >> files.txt
}

# Function that downloads TROPOMI data for a given month and year
download_tropomi () {
    # inputs of month and year
    Year=$1
    Month=$2
    LastDay=$(cal $Month $Year | awk 'NF {DAYS = $NF}; END{print DAYS}')
    Month=$(printf "%02d" $Month)
    mkdir -p ${StorageDir}/tropomi/${Year}-${Month}

    # form a list of urls to download
    touch files.txt
    prev_length=-1
    s=0
    while true; do
        if [[ $Year -lt 2022 || ($Year -eq 2022 && $Month -lt 07) ]]; then # pre July 2022, everything is RPRO/v02.04.00
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Reprocessing AND processorversion:020400 AND beginposition:[${Year}-${Month}-01T00:00:00.000Z TO ${Year}-${Month}-${LastDay}T23:59:59.999Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
        elif [[ $Year -eq 2022 && $Month -eq 07 ]]; then # July 2022 is a mix of RPRO/v02.04.00 and OFFL/v02.04.00
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Reprocessing AND processorversion:020400 AND beginposition:[2022-07-01T00:00:00.000Z TO 2022-07-26T00:17:00.000Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Offline AND processorversion:020400 AND beginposition:[2022-07-26T00:17:00.000Z TO 2022-07-31T23:59:59.999Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
        elif [[ ($Year -eq 2022 && $Month -gt 07) || ($Year -eq 2023 && $Month -lt 03) ]]; then # August 2022-February 2023 is OFFL/v02.04.00
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Offline AND processorversion:020400 AND beginposition:[${Year}-${Month}-01T00:00:00.000Z TO ${Year}-${Month}-${LastDay}T23:59:59.999Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
        elif [[ $Year -eq 2023 && $Month -eq 03 ]]; then # March 2023 is a mix of OFFL/v02.04.00 and OFFL/v02.05.00
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Offline AND processorversion:020400 AND beginposition:[2023-03-01T00:00:00.000Z TO 2023-03-12T02:00:00.000Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Offline AND processorversion:020500 AND beginposition:[2023-03-12T02:00:00.000Z TO 2023-03-31T23:59:59.999Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
        else # March 2023-Present is OFFL/v02.05.00
            wget -q --no-check-certificate --user=s5pguest --password=s5pguest --output-document="output.txt" "https://s5phub.copernicus.eu/dhus/search?q=platformname:Sentinel-5 AND producttype:L2__CH4___ AND processingmode:Offline AND processorversion:020500 AND beginposition:[${Year}-${Month}-01T00:00:00.000Z TO ${Year}-${Month}-${LastDay}T23:59:59.999Z]&rows=100&start=$s"
            append_output_txt_to_files_txt
        fi
        length=$(wc -l < files.txt)
        if [ "$length" -eq "$prev_length" ]; then
            break
        fi
        prev_length=$length
        s=$((s+100))
    done
    sed -i -e 's/<link href=//g' files.txt
    sed -i -e 's/\/>//g' files.txt

    # download tropomi data with a maximum of 48 wget running simultaneously
    xargs -n 1 -P 48 wget --content-disposition --continue --no-check-certificate --tries=5 --user=s5pguest --password=s5pguest -P ${StorageDir}/tropomi/${Year}-${Month} < files.txt

    # remove text files
    rm files.txt
    rm output.txt
}

write_blended () {
    Year=$1
    Month=$2
    Month=$(printf "%02d" $Month)
    mkdir -p ${StorageDir}/blended/${Year}-${Month}
    conda activate blnd_env
    python write_blended_files.py
}
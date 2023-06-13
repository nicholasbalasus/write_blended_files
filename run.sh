#!/bin/bash

#SBATCH -t 120
#SBATCH -c 48
#SBATCH --mem 48000
#SBATCH -p huce_cascade

# Read config file and get functions
source utils.sh
eval $(parse_yaml config.yml)

# Get access to miniconda and mamba solver
source ~/.bashrc
conda install -c conda-forge mamba
if conda env list | grep -q "blnd_env"; then # update env if it exists
  mamba env update -f blnd_env.yml
else # if it doesn't exist, make a new one
  mamba env create -f blnd_env.yml
fi

# Get the uncompressed model_lgbm.pkl file
gunzip -k model_lgbm.pkl.gz

# Download the TROPOMI data for the given month and year
download_tropomi $Year $Month

# Write the Blended data for the given month and year
write_blended $Year $Month

# Remove the uncompressed model_lgbm.pkl file
rm model_lgbm.pkl
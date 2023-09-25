These scripts write one month of data for the blended TROPOMI+GOSAT product as described in [Balasus et al. (2023)](https://doi.org/10.5194/amt-2023-47). The file `model_lgbm.pkl.gz` and associated corrections (`a` and `b` in `config.yml`) come from the above paper (and thus from [this](https://github.com/nicholasbalasus/blended_tropomi_gosat_methane) code).

1. Create the `blnd_env` environment.
    - Install [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html).
    - Install `mamba` in the `base` environment using `conda install -c conda-forge mamba`.
    - Run `mamba env create -f blnd_env.yml`.
2. Make an account at [https://dataspace.copernicus.eu/](https://dataspace.copernicus.eu/).
3. Put your email and password in `~/.netrc` like this `machine identity.dataspace.copernicus.eu login <email> password <password>`.
4. Specify the year and months of data you want in config.yml.
5. Run `sbatch run.sh`.
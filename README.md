These scripts write one month of data for the blended TROPOMI+GOSAT product as described in [Balasus et al. (2023)](https://doi.org/10.5194/amt-16-3787-2023). The file `model_lgbm.pkl.gz` and associated corrections (`a` and `b` in `config.py`) come from the above paper (and thus from [this](https://github.com/nicholasbalasus/blended_tropomi_gosat_methane) code).

1. Create the `blnd_env` environment.
    - First, install [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html).
    - Then, run this from the command line:
    ```
    conda install -c conda-forge mamba
    mamba env create -f environment.yml
    ```
2. Set up a file of AWS credentials at `~/.aws/config` for the [Copernicus Data Space Ecosystem](https://documentation.dataspace.copernicus.eu/APIs/S3.html) (CDSE). There is a 6 TB per month download limit for this data source.
3. Run the script `run.sh`.
    - First, this will download the TROPOMI data from the CDSE.
    - Then, it will use those files to write blended files.
These scripts write one month of data for the blended TROPOMI+GOSAT product as described in [Balasus et al. (2023)](https://doi.org/10.5194/amt-16-3787-2023). The file `model_lgbm.pkl.gz` and associated corrections (`a` and `b` in `config.py`) come from the above paper (and thus from [this](https://github.com/nicholasbalasus/blended_tropomi_gosat_methane) code).

1. Create the `blnd_env` environment.
    - First, install [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html).
    - Then, run this from the command line:
    ```
    conda install -c conda-forge mamba
    mamba env create -f resources/environment.yml
    ```
2. Set up a file of AWS credentials at `~/.aws/config` for the [Copernicus Data Space Ecosystem](https://documentation.dataspace.copernicus.eu/APIs/S3.html) (CDSE). There is a 6 TB per month download limit for this data source.
3. Set the month you want to generate data for in `config.py` as well as the directory to save them to.
4. Extract the model to use for correction.
    ```
    gunzip -k "resources/model_lgbm.pkl.gz"
    ```
5. Download TROPOMI data for this month.
    ```
    sbatch -J download -p sapphire -t 1-00:00 --mem 32G -c 4\
       --wrap "source ~/.bashrc; conda activate blnd_env; \
       python -B -m scripts.download_tropomi"
    ```
6. Generate the blended TROPOMI+GOSAT data using the downloaded files.
    - Run this from the command line:
    ```
    sbatch -J write -p sapphire,bigmem -t 1-00:00 --mem 1000G -c 112\
        --wrap "source ~/.bashrc; conda activate blnd_env;\
        python -B -m scripts.write_blended_files"
    ```
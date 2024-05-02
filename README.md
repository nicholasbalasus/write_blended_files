These scripts write one month of data for the blended TROPOMI+GOSAT product as described in [Balasus et al. (2023)](https://doi.org/10.5194/amt-16-3787-2023). The file `model_lgbm.pkl.gz` and associated corrections (`a` and `b` in `config.py`) come from the above paper (and thus from [this](https://github.com/nicholasbalasus/blended_tropomi_gosat_methane) code).

1. Create the `blnd_env` environment.
    - Install [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html).
    - Run `micromamba create -f resources/environment.yml`.
2. Set up a file of AWS credentials at `~/.aws/config` for the [Copernicus Data Space Ecosystem](https://documentation.dataspace.copernicus.eu/APIs/S3.html) (CDSE). There is a 6 TB per month download limit for this data source. `~/.aws/config` should look like this:
    ```
    [default]
    aws_access_key_id = [access key from CDSE]
    aws_secret_access_key = [secret key from CDSE]
    ```
3. Set the month you want to generate data for in `config.py` as well as the directory to save them to.
4. Extract the model to use for correction.
    ```
    gunzip -k "resources/model_lgbm.pkl.gz"
    ```
5. Download TROPOMI data for this month.
    ```
    sbatch -J download -p huce_cascade -t 1-00:00 --mem 64G -c 4\
       --wrap "source ~/.bashrc; micromamba activate blnd_env; \
       python -B -m scripts.download_tropomi"
    ```
6. Generate the blended TROPOMI+GOSAT data using the downloaded files.
    ```
    sbatch -J write -p huce_cascade -t 0-08:00 --mem 184G -c 48\
        --wrap "source ~/.bashrc; micromamba activate blnd_env;\
        python -B -m scripts.write_blended_files"
    ```
These scripts write one month of data for the blended TROPOMI+GOSAT product as described in [Balasus et al. (2023)](https://doi.org/10.5194/amt-2023-47). The file `model_lgbm.pkl.gz` and associated corrections (`a` and `b` in `config.yml`) come from the above paper (and thus from [this](https://github.com/nicholasbalasus/blended_tropomi_gosat_methane) code).

1. Specify the year and month of data you want in config.yml.
2. Run `sbatch run.sh`.
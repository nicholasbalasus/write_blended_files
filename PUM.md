### Product User Manual for the Blended TROPOMI+GOSAT Product
Nicholas Balasus
7 July 2023

(1) Introduction
The blended TROPOMI+GOSAT files are formed by applying the correction described in Balasus et al. (2023) to the variable `methane_mixing_ratio_bias_corrected` in the operational TROPOMI files. This adds the new variable of `methane_mixing_ratio_blended`. The correction is applicable to the files with a processor version of 02.04.00, 02.05.00, or 02.06.00 and to observations in those files with `qa_value` == 1.0. The following sections describe downloading the data, the file names, the file contents, and how to plot the file contents using Python.
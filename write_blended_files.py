from netCDF4 import Dataset
import pandas as pd
import os
import numpy as np
import glob
import yaml
import pickle
import multiprocessing
import sys

# Function to turn one netCDF TROPOMI file into one pandas dataframe
def get_tropomi_df(tropomi_file):
    
    with Dataset(tropomi_file) as ds:
        mask = ds["PRODUCT/qa_value"][:] == 1.0
        tropomi_df = pd.DataFrame({
                           # non-predictor variables
                           "latitude": ds["PRODUCT/latitude"][:][mask],
                           "longitude": ds["PRODUCT/longitude"][:][mask],
                           "time": np.expand_dims(np.tile(ds["PRODUCT/time_utc"][:][0,:], (mask.shape[2],1)).T, axis=0)[mask],
                           "latitude_bounds": list(ds["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/latitude_bounds"][:][mask]),
                           "longitude_bounds": list(ds["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/longitude_bounds"][:][mask]),
                           "xch4": ds["PRODUCT/methane_mixing_ratio"][:][mask],
                           "xch4_corrected": ds["PRODUCT/methane_mixing_ratio_bias_corrected"][:][mask],
                           "pressure_interval": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/pressure_interval"][:][mask],
                           "surface_pressure": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/surface_pressure"][:][mask],
                           "dry_air_subcolumns": list(ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/dry_air_subcolumns"][:][mask]),
                           "methane_profile_apriori": list(ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/methane_profile_apriori"][:][mask]),
                           "column_averaging_kernel": list(ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/column_averaging_kernel"][:][mask]),
                           # predictor variables
                           "solar_zenith_angle": ds["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/solar_zenith_angle"][:][mask],
                           "relative_azimuth_angle": np.abs(180 - np.abs(ds["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/solar_azimuth_angle"][:][mask] -
                                                                         ds["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/viewing_azimuth_angle"][:][mask])),
                           "across_track_pixel_index": np.expand_dims(np.tile(ds["PRODUCT/ground_pixel"][:], (mask.shape[1],1)), axis=0)[mask],
                           "surface_classification": (ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/surface_classification"][:][mask] & 0x03).astype(int),
                           "surface_altitude": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/surface_altitude"][:][mask],
                           "surface_altitude_precision": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/surface_altitude_precision"][:][mask],
                           "eastward_wind": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/eastward_wind"][:][mask],
                           "northward_wind": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/northward_wind"][:][mask],
                           "xch4_apriori": np.sum(ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/methane_profile_apriori"][:][mask]/
                                                  np.expand_dims(np.sum(ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/dry_air_subcolumns"][:][mask], axis=1),axis=1), axis=1)*1e9,
                           "reflectance_cirrus_VIIRS_SWIR": ds["PRODUCT/SUPPORT_DATA/INPUT_DATA/reflectance_cirrus_VIIRS_SWIR"][:][mask],
                           "xch4_precision": ds["PRODUCT/methane_mixing_ratio_precision"][:][mask],
                           "fluorescence": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/fluorescence"][:][mask],
                           "co_column": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/carbonmonoxide_total_column"][:][mask],
                           "co_column_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/carbonmonoxide_total_column_precision"][:][mask],
                           "h2o_column": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/water_total_column"][:][mask],
                           "h2o_column_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/water_total_column_precision"][:][mask],
                           "aerosol_size": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_size"][:][mask],
                           "aerosol_size_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_size_precision"][:][mask],
                           "aerosol_height": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_mid_altitude"][:][mask],
                           "aerosol_height_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_mid_altitude_precision"][:][mask],
                           "aerosol_column": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_number_column"][:][mask],
                           "aerosol_column_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_number_column_precision"][:][mask],
                           "surface_albedo_SWIR": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/surface_albedo_SWIR"][:][mask],
                           "surface_albedo_SWIR_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/surface_albedo_SWIR_precision"][:][mask],
                           "surface_albedo_NIR": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/surface_albedo_NIR"][:][mask],
                           "surface_albedo_NIR_precision": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/surface_albedo_NIR_precision"][:][mask],
                           "aerosol_optical_thickness_SWIR": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_optical_thickness_SWIR"][:][mask],
                           "aerosol_optical_thickness_NIR": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/aerosol_optical_thickness_NIR"][:][mask],
                           "chi_square_SWIR": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/chi_square_SWIR"][:][mask],
                           "chi_square_NIR": ds["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/chi_square_NIR"][:][mask]
                          })

    # Convert column of strings to datetime
    tropomi_df["time"] = pd.to_datetime(tropomi_df["time"], format="%Y-%m-%dT%H:%M:%S.%fZ")
    
    return tropomi_df

# Function to predict delta_tropomi_gosat using model_lgbm.pkl
def predict_delta_tropomi_gosat(tropomi_file, model):
    
    df = get_tropomi_df(tropomi_file)
    # Get rid of the non-predictor variables
    df = df.drop(["latitude","longitude","time","latitude_bounds","xch4","xch4_corrected","pressure_interval","surface_pressure","dry_air_subcolumns","methane_profile_apriori","column_averaging_kernel"], axis=1) 
    df = df.add_prefix("tropomi_")
    delta_tropomi_gosat = (config["a"]*model.predict(df) + config["b"])

    return delta_tropomi_gosat

# Function to write a BLND file given a RPRO or OFFL file
def f_write_blended_files(src_file):

    # new file will have the same name but with BLND as the acronym and the creation time changed
    dst_file = src_file.split("/")[-1].replace("RPRO","BLND").replace("OFFL", "BLND")
    dst_file = os.path.join(config["StorageDir"], f"{year}-{(str(month)).zfill(2)}", "blended", dst_file[:dst_file.rfind("_")+1]+pd.Timestamp.utcnow().strftime("%Y%m%dT%H%M%S")+".nc")

    # remove dst_file if it already exists (weird notation is because the time generated portion of the filename is unique)
    [os.remove(file) for file in glob.glob(dst_file[:dst_file.rfind("_")+1]+"*")]

    print(f"Writing {dst_file}", flush=True)

    with Dataset(src_file) as src, Dataset(dst_file, "w") as dst:
    
        # Make sure this is a valid applciation of model_lgbm.pkl
        assert src.processor_version in ["2.4.0", "2.5.0"]

        # Set global attributes
        dst.setncatts({
            "Title": "Blended TROPOMI+GOSAT Methane Product",
            "Contact": "Nicholas Balasus (nicholasbalasus@g.harvard.edu)"
        })

        # Create a mask to select data
        mask = src["PRODUCT/qa_value"][:] == 1.0
        
        # Create nobs dimension (dimension across which qa_value == 1.0) and layer dimension
        dst.createDimension("nobs", np.sum(mask))
        dst.createDimension("layer", len(src["PRODUCT/layer"]))
        dst.createDimension("corner", len(src["PRODUCT/corner"]))
        
        # Copy over variables and their attributes from the PRODUCT group
        vars_to_keep_in_PRODUCT = ["qa_value","latitude","longitude","methane_mixing_ratio","methane_mixing_ratio_precision",
                                   "methane_mixing_ratio_bias_corrected"]
        for var in vars_to_keep_in_PRODUCT:
            dst.createVariable(var, src["PRODUCT/"+var].datatype, ('nobs'))
            dst[var].setncatts(src["PRODUCT/"+var].__dict__)
            dst[var][:] = src["PRODUCT/"+var][:][mask]
            
        # Time originally has only scanline dimensions, so need to expand it
        dst.createVariable("time_utc", np.str_, ('nobs'), fill_value='')
        dst["time_utc"].setncatts({'long_name': 'Time of observation as ISO 8601 date-time string'})
        dst["time_utc"][:] = np.array(np.expand_dims(np.tile(src["PRODUCT/time_utc"][:][0,:], (mask.shape[2],1)).T, axis=0), dtype=np.str_)[mask]
        
        # Copy over variables and their attributes from the PRODUCT/SUPPORT_DATA/GEOLOCATIONS group
        vars_to_keep_in_PRODUCT_SUPPORT_DATA_GEOLOCATIONS = ["latitude_bounds","longitude_bounds"]
        for var in vars_to_keep_in_PRODUCT_SUPPORT_DATA_GEOLOCATIONS:
            dst.createVariable(var, src["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/"+var].datatype, ('nobs', 'corner'))
            dst[var].setncatts(src["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/"+var].__dict__)
            dst[var][:] = src["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/"+var][:][mask]
            
        # Copy over variables and their attributes from the PRODUCT/SUPPORT_DATA/DETAILED_RESULTS group
        vars_to_keep_in_PRODUCT_SUPPORT_DATA_DETAILED_RESULTS = ["chi_square_SWIR","surface_albedo_SWIR","surface_albedo_NIR",
                                                                 "surface_albedo_SWIR_precision","surface_albedo_NIR_precision",
                                                                 "aerosol_size","aerosol_size_precision"]
        for var in vars_to_keep_in_PRODUCT_SUPPORT_DATA_DETAILED_RESULTS:
            dst.createVariable(var, src["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/"+var].datatype, ('nobs'))
            dst[var].setncatts(src["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/"+var].__dict__)
            dst[var][:] = src["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/"+var][:][mask]
            
        vars_to_keep_in_PRODUCT_SUPPORT_DATA_DETAILED_RESULTS = ["column_averaging_kernel"]
        for var in vars_to_keep_in_PRODUCT_SUPPORT_DATA_DETAILED_RESULTS:
            dst.createVariable(var, src["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/"+var].datatype, ('nobs','layer'))
            dst[var].setncatts(src["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/"+var].__dict__)
            dst[var][:] = src["PRODUCT/SUPPORT_DATA/DETAILED_RESULTS/"+var][:][mask]
        
        # Copy over variables and their attributes from the PRODUCT/SUPPORT_DATA/INPUT_DATA group
        vars_to_keep_in_PRODUCT_SUPPORT_DATA_INPUT_DATA = ["surface_altitude","surface_altitude_precision",
                                                           "surface_classification","surface_pressure",
                                                           "pressure_interval","reflectance_cirrus_VIIRS_SWIR"]
        for var in vars_to_keep_in_PRODUCT_SUPPORT_DATA_INPUT_DATA:
            dst.createVariable(var, src["PRODUCT/SUPPORT_DATA/INPUT_DATA/"+var].datatype, ('nobs'))
            dst[var].setncatts(src["PRODUCT/SUPPORT_DATA/INPUT_DATA/"+var].__dict__)
            dst[var][:] = src["PRODUCT/SUPPORT_DATA/INPUT_DATA/"+var][:][mask]
            
        vars_to_keep_in_PRODUCT_SUPPORT_DATA_INPUT_DATA = ["methane_profile_apriori","dry_air_subcolumns"]
        for var in vars_to_keep_in_PRODUCT_SUPPORT_DATA_INPUT_DATA:
            dst.createVariable(var, src["PRODUCT/SUPPORT_DATA/INPUT_DATA/"+var].datatype, ('nobs', 'layer'))
            dst[var].setncatts(src["PRODUCT/SUPPORT_DATA/INPUT_DATA/"+var].__dict__)
            dst[var][:] = src["PRODUCT/SUPPORT_DATA/INPUT_DATA/"+var][:][mask]
            
        # Edit some of the attributes to be consistent with the new file format
        for var in dst.variables:
            if var == "time_utc":
                dst[var].setncattr("coordinates", "longitude latitude")
                
            for attribute in dst[var].ncattrs():
                if attribute == "coordinates":
                    dst[var].setncattr(attribute, "longitude latitude")
                if attribute == "bounds" and var == "latitude":
                    dst[var].setncattr(attribute, "latitude_bounds")
                if attribute == "bounds" and var == "longitude":
                    dst[var].setncattr(attribute, "longitude_bounds")
                if attribute == "comment" and var == "methane_mixing_ratio_bias_corrected":
                    del dst[var].comment
                    del dst[var].ancillary_variables
                if attribute == "ancillary_variables" and var == "methane_mixing_ratio":
                    del dst[var].ancillary_variables
                    
        # Add blended xch4
        dst.createVariable("methane_mixing_ratio_blended", src["PRODUCT/methane_mixing_ratio"].datatype, ('nobs'))
        dst["methane_mixing_ratio_blended"].setncatts(src["PRODUCT/methane_mixing_ratio"].__dict__)
        dst["methane_mixing_ratio_blended"].setncattr("comment", "produced as described in Balasus et al. (2023)")
        if np.sum(mask) == 0:
            # Set to be empty because model.predict fails with an empty dataframe
            dst["methane_mixing_ratio_blended"][:] = src["PRODUCT/methane_mixing_ratio_bias_corrected"][:][mask]
        else:
            with open(cwd+"/model_lgbm.pkl", "rb") as handle:
                model = pickle.load(handle)
            dst["methane_mixing_ratio_blended"][:] = src["PRODUCT/methane_mixing_ratio_bias_corrected"][:][mask] - predict_delta_tropomi_gosat(src_file, model)

if __name__ == "__main__":

    cwd = sys.argv[1]
    year = sys.argv[2]
    month = sys.argv[3]

    with open(cwd+"/config.yml", "r") as f:
        config = yaml.safe_load(f)

    # Write BLND files using as many cores as you have
    src_files = sorted(glob.glob(os.path.join(config["StorageDir"], f"{year}-{(str(month)).zfill(2)}", "tropomi", "*.nc")))
    num_processes = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(f_write_blended_files, src_files)
        pool.close()
        pool.join()
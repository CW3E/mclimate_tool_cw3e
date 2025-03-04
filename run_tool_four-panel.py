"""
Filename:    run_tool.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: For GFS, compare IVT to model climate every 6 hours for the next 10 days
"""

## import libraries
import os, sys
import yaml
import xarray as xr
import pandas as pd
import numpy as np
from datetime import timedelta
import re
import shutil
import glob
from multiprocessing import Pool

import matplotlib as mpl
mpl.use('agg')

# import personal modules
from plotter import plot_mclimate_forecast
import mclimate_funcs as mclim_func
from build_html_table import create_html_table
from read_ensemble_data import load_GEFS_datasets
from cw3e_tools import remove_tmp_data_files
from plot_four_panel_fig import create_dataframe_max_value, plot_heatmap

sys.argv.append(None) ## add this in case date not specified in command line
fdate = sys.argv[1] ## set this to None to get most recently downloaded data  

#################################
### CHECK TO REMOVE TMP FILES ###
#################################
print('Removing tmp intermediate data files...') 
# Specify the directory and the pattern
directory = "/data/projects/operations/GEFS_Mclimate/data/tmp/"
pattern = "tmp*.nc"  # Delete all .txt files
remove_tmp_data_files(directory, pattern)

######################
### VARS TO UPDATE ###
######################
model = 'GEFS' ## 'GEFSv12_reforecast', 'GFS', 'GEFS', 'GEFS_archive'
fig_path = '/data/projects/operations/GEFS_mclimate/figs/images_operational/'
os.makedirs(os.path.dirname(fig_path), exist_ok=True)

################
### READ IVT ###
################
print('...Reading IVT data for M-Climate comparison')
varname = 'ivt' ## 'freezing_level' or 'ivt'
forecast, ds = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')
step_lst = ds.step.values
    
##############################################################
### PREPROCESS INTERMEDIATE GEFS FREEZING LEVEL AND UV1000 ###
##############################################################
print('...preprocess Intermediate GEFS data ...')
F_lst =  step_lst
ts = pd.to_datetime(forecast.init_date.values, format="%Y%m%d%H")
fdate = ts.strftime('%Y%m%d%H')
print(fdate)

def multiP_preprocess_GEFS_intermediate(F):
    ##############################
    ### PREP INTERMEDIATE DATA ###
    ##############################
    print('... Loading data for {0} hour lead'.format(F))
    s = load_GEFS_datasets(F=F, fdate=fdate)
    model_data= s.calc_vars()

if __name__ == '__main__':      
    with mp.Pool(processes=16) as pool:
            pool.map(multiP_preprocess_GEFS_intermediate,F_lst)
            pool.close()
            pool.join()

##############################
### LOAD INTERMEDIATE DATA ###
##############################
    
print('...Reading Freezing Level data for M-Climate comparison')
varname = 'freezing_level'
forecast1, ds1 = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')

print('...Reading UV data for M-Climate comparison')
varname = 'uv1000'
forecast2, ds2 = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')


### merge the datasets
ds3 = xr.merge([ds, ds1, ds2])
ds3 = ds3.sortby('lat')

fc = xr.merge([forecast, forecast1, forecast2])
fc = fc.sortby('lat')

####################
### CREATE PLOTS ###
####################
print(' ...... creating four panel plot ...')
step_lst = ds3.step.values
for i, step in enumerate(step_lst):
    print(step)
    out_fname = fig_path + 'SEAK_mclimate_F{0}'.format(step)
    plot_mclimate_forecast_four_panel(ds3, fc, step, out_fname, domain="SEAK")
    out_fname = fig_path + 'NPAC_mclimate_F{0}'.format(step)
    plot_mclimate_forecast_four_panel(ds3, fc, step, out_fname, domain="NPAC")

## create dataframe with max values
print(' ...... creating dataframe with maximum values ...')
df, init_time, date_lbl = create_dataframe_max_values(ds3)

######################
### CREATE HEATMAP ###
######################
print(' ...... creating heatmap ...')
out_fname = fig_path + 'heatmap'
plot_heatmap(df, init_time, date_lbl, fdate, out_fname)
        
########################
### REMOVE TMP FILES ###
########################
print('Removing tmp intermediate data files...') 
# Specify the directory and the pattern
directory = "/data/projects/operations/GEFS_Mclimate/data/tmp/"
pattern = "tmp*.nc"  # Delete all .txt files
remove_tmp_data_files(directory, pattern)
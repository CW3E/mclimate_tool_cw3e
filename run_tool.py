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
import multiprocessing as mp

import matplotlib as mpl
mpl.use('agg')

# import personal modules
import mclimate_funcs as mclim_func
from read_ensemble_data import load_GEFS_datasets
from cw3e_tools import remove_tmp_data_files
from plot_four_panel_fig import plot_mclimate_forecast_four_panel, compute_AR_duration_AR_impact_index

sys.argv.append(None) ## add this in case date not specified in command line
fdate = sys.argv[1] ## set this to None to get most recently downloaded data  

#################################
### CHECK TO REMOVE TMP FILES ###
#################################
print('Removing tmp intermediate data files...') 
# Specify the directory and the pattern
directory = "/data/projects/operations/GEFS_Mclimate/data/tmp/"
pattern = "*tmp*.nc"  # Delete all .txt files
remove_tmp_data_files(directory, pattern)

######################
### VARS TO UPDATE ###
######################
model = 'GEFS' ## 'GEFSv12_reforecast', 'GFS', 'GEFS', 'GEFS_archive'
fig_path = '/data/projects/operations/GEFS_Mclimate/figs/images_operational/'
# fig_path = '/data/projects/website/mirror/htdocs/Projects/MClimate/images/images_operational/'
# os.makedirs(os.path.dirname(fig_path), exist_ok=True)

################
### READ IVT ###
################
print('...Reading IVT data for M-Climate comparison')
varname = 'ivt' ## 'freezing_level' or 'ivt'
forecast, ds = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')
step_lst = ds.step.values
ds = ds.rename({'mclimate': 'ivt'})
    
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
            
            
######################
### PREPROCESS QPF ###
######################
s = load_GEFS_datasets(F=None, fdate=fdate)
model_data = s.calc_qpf()

##############################
### LOAD INTERMEDIATE DATA ###
##############################
    
print('...Reading Freezing Level data for M-Climate comparison')
varname = 'freezing_level'
forecast1, ds1 = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')
ds1 = ds1.rename({'mclimate': 'freezing_level'})

print('...Reading UV data for M-Climate comparison')
varname = 'uv1000'
forecast2, ds2 = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')
ds2 = ds2.rename({'mclimate': 'uv'})

print('...Reading QPF data for M-Climate comparison')
varname = 'qpf'
forecast3, ds3 = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')
ds3 = ds3.rename({'mclimate': 'qpf'})


### merge the datasets
ds_final = xr.merge([ds, ds1, ds2, ds3])
ds_final = ds_final.sortby('lat')

## compute AR duration and AR Impact Index value
ds_final = compute_AR_duration_AR_impact_index(ds_final)

fc = xr.merge([forecast, forecast1, forecast2])
fc = fc.sortby('lat')

####################
### CREATE PLOTS ###
####################
print(' ...... creating four panel plot ...')
step_lst = ds_final.step.values
for i, step in enumerate(step_lst):
    print(step)
    out_fname = fig_path + 'SEAK_mclimate_F{0}'.format(step)
    plot_mclimate_forecast_four_panel(ds_final, fc, step, out_fname, domain="SEAK", impact_date=None, fdate=fdate)
    out_fname = fig_path + 'NPAC_mclimate_F{0}'.format(step)
    plot_mclimate_forecast_four_panel(ds_final, fc, step, out_fname, domain="NPAC", impact_date=None, fdate=fdate)

        
########################
### REMOVE TMP FILES ###
########################
print('Removing tmp intermediate data files...') 
# Specify the directory and the pattern
directory = "/data/projects/operations/GEFS_Mclimate/data/tmp/"
pattern = "tmp*.nc"  # Delete all .txt files
remove_tmp_data_files(directory, pattern)
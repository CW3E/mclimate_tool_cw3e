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
fdate = None ## initialization date in YYYYMMDD format
model = 'GEFS' ## 'GEFSv12_reforecast', 'GFS', 'GEFS', 'GEFS_archive'
fig_path = '/data/projects/website/mirror/htdocs/Projects/MClimate/images/images_operational/'
os.makedirs(os.path.dirname(fig_path), exist_ok=True)

###########
### IVT ###
###########
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

def multiP_preprocess_GEFS_intermediate(F, fdate):
    ##############################
    ### PREP INTERMEDIATE DATA ###
    ##############################
    print('... Loading data for {0} hour lead'.format(F))
    s = load_GEFS_datasets(F=F, fdate=fdate)
    model_data= s.calc_vars()

if __name__ == '__main__':
    with Pool(processes=30) as pool:
        for F in F_lst:
            result = pool.apply_async(func=multiP_preprocess_GEFS_intermediate,args=(F, fdate))
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

####################
### CREATE PLOTS ###
####################

var_lst = ['ivt', 'freezing_level', 'uv1000']
ds_lst = [ds, ds1, ds2]
fc_lst = [forecast, forecast1, forecast2]
region_lst = ['NPAC', 'SEAK']

print('...Writing plots')
for i, (varname, ds, fc) in enumerate(zip(var_lst, ds_lst, fc_lst)):
    for region in region_lst:
        for step in step_lst:
            print('...for {0}, {1}, {2}'.format(varname, region, step))
            out_fname = fig_path + '{2}_{0}_mclimate_F{1}'.format(varname, step, region)
            ## write plots
            plot_mclimate_forecast(ds, fc, step=step, varname=varname, fname=out_fname, ext_name=region)

###################
### BUILD TABLE ###
###################
## put into single dataset for table
ds = ds.rename({'mclimate': 'ivt'})
ds1 = ds1.rename({'mclimate': 'freezing_level'})
ds2 = ds2.rename({'mclimate': 'uv'})
ds3 = xr.merge([ds, ds1, ds2])
ds3 = ds3.sortby('lat')

print('...Building Table')
for i, region in enumerate(region_lst):           
    df = create_html_table(ds3, region)
    ## convert to html
    df_html = df.to_html(index=False, formatters={'Hour': lambda x: '<b>' + x + '</b>'}, escape=False)



    #######################
    ### WRITE HTML FILE ###
    #######################
    print('...Writing HTML file')
    out_fname = "/data/projects/website/mirror/htdocs/Projects/MClimate/mclimate_tool_operational.html"
    out_fname = "/data/projects/website/mirror/htdocs/Projects/MClimate/mclimate_beta_{0}.html".format(region)

    with open('/data/projects/operations/GEFS_Mclimate/out/html_text.txt', mode='r') as in_file, \
         open('/data/projects/operations/GEFS_Mclimate/out/html_text2_{0}.txt'.format(region), mode='r') as in_file2, \
         open(out_fname, mode='w') as out_file:

        # A file is iterable
        # We can read each line with a simple for loop
        for line in in_file:
            out_file.write(line)


        ## now add in the table
        out_file.write(df_html)

        ## now add the last few lines
        for line in in_file2:
            out_file.write(line)

        out_file.close()
        
########################
### REMOVE TMP FILES ###
########################
print('Removing tmp intermediate data files...') 
# Specify the directory and the pattern
directory = "/data/projects/operations/GEFS_Mclimate/data/tmp/"
pattern = "tmp*.nc"  # Delete all .txt files
remove_tmp_data_files(directory, pattern)
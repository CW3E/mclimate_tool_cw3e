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

import glob
%matplotlib inline

import matplotlib as mpl
mpl.use('agg')

# import personal modules
from plotter import plot_mclimate_forecast
import mclimate_funcs as mclim_func
from cw3e_tools import load_GFS_datasets
from build_html_table import create_html_table

#########################
### BUILD IVT DATASET ###
#########################

varname = 'ivt'

s = load_GFS_datasets(varname)
forecast = s.calc_vars()

## get month and date from the intialization date
ts = pd.to_datetime(forecast.init_date.values, format="%Y%m%d%H")
mon = ts.strftime('%m')
day = ts.strftime('%d')
print(mon, day)

## load mclimate data
mclimate = mclim_func.load_mclimate(mon, day, varname)

## compare the mclimate to the reforecast
ds = mclim_func.compare_mclimate_to_forecast(forecast, mclimate, varname)


## create plots every 6 hours
step_lst = ds.step.values
for i, step in enumerate(step_lst):
    print(step)
    plot_mclimate_forecast(ds, forecast, step=step)

########################
### BUILD Z0 DATASET ###
########################

varname = 'freezing_level'
date_string = ts.strftime('%Y%m%d%H') # the datestring from IVT dataset
s = load_GFS_datasets(varname, fdate=date_string) # match the time of the IVT dataset
forecast = s.calc_vars()

## load mclimate data
mclimate = mclim_func.load_mclimate(mon, day, varname)

## compare the mclimate to the reforecast
ds1 = mclim_func.compare_mclimate_to_forecast(forecast, mclimate, varname)

for i, step in enumerate(step_lst):
    print(step)
    plot_mclimate_forecast(ds1, forecast, step=step, varname=varname)

######################
### MERGE DATASETS ###
######################

ds = ds.rename({'mclimate': 'IVT'})
ds1 = ds1.rename({'mclimate': 'freezing_level'})
ds2 = xr.merge([ds, ds1])
    
## build interactive html table based on subregion
ext_SEAK = [-141., -130., 54.5, 60.] # extent of SEAK 
df = create_html_table(ds2, ext_SEAK)

## write table to text file
html = df.to_html(index=False, formatters={'Hour': lambda x: '<b>' + x + '</b>'}, escape=False)

# write html to file
text_file = open("out/table.html", "w")
text_file.write(html)
text_file.close()
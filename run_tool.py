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

step_lst = ds.step.values

for i, step in enumerate(step_lst):
    print(step)
    plot_mclimate_forecast(ds, forecast, step=step)
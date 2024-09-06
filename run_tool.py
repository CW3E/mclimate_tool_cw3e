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

import matplotlib as mpl
mpl.use('agg')

# import personal modules
from plotter import plot_mclimate_forecast
import mclimate_funcs as mclim_func
from build_html_table import create_html_table


######################
### VARS TO UPDATE ###
######################
fdate = None ## initialization date in YYYYMMDD format
model = 'GEFS' ## 'GEFSv12_reforecast', 'GFS', 'GEFS', 'GEFS_archive'
map_ext = [-170., -120., 40., 65.] ## map extent [minlon, maxlon, minlat, maxlat]
table_ext = [-141., -130., 54.5, 60.] ## extent to choose the maximum value from for the table [minlon, maxlon, minlat, maxlat]
fig_path = '/data/projects/website/mirror/htdocs/Projects/MClimate/images/images_operational/'
os.makedirs(os.path.dirname(fig_path), exist_ok=True)

###########
### IVT ###
###########
print('...Reading IVT data for M-Climate comparison')
varname = 'ivt' ## 'freezing_level' or 'ivt'
forecast, ds = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')
step_lst = ds.step.values

print('...Writing IVT plots')
for i, step in enumerate(step_lst):
    print(step)
    out_fname = fig_path + '{0}_mclimate_F{1}'.format(varname, step)
    plot_mclimate_forecast(ds, forecast, step=step, varname='ivt', fname=out_fname, ext=map_ext)

######################
### FREEZING LEVEL ###
######################
print('...Reading Freezing Level data for M-Climate comparison')
varname = 'freezing_level'
model = 'GEFS'
ts = pd.to_datetime(forecast.init_date.values, format="%Y%m%d%H")
fdate = ts.strftime('%Y%m%d%H')
forecast, ds1 = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='skyriver')

print('...Writing Freezing Level plots')
for i, step in enumerate(step_lst):
    print(step)
    out_fname = fig_path + '{0}_mclimate_F{1}'.format(varname, step)
    plot_mclimate_forecast(ds1, forecast, step=step, varname='freezing_level', fname=out_fname, ext=[-141., -130., 54., 60.])

## put into single dataset for table
ds = ds.rename({'mclimate': 'IVT'})
ds1 = ds1.rename({'mclimate': 'freezing_level'})
ds2 = xr.merge([ds, ds1])
ds2 = ds2.sortby('lat')

###################
### BUILD TABLE ###
###################
print('...Building Table')
df = create_html_table(ds2, table_ext)
## convert to html
df_html = df.to_html(index=False, formatters={'Hour': lambda x: '<b>' + x + '</b>'}, escape=False)


#######################
### WRITE HTML FILE ###
#######################
print('...Writing HTML file')
out_fname = "/data/projects/website/mirror/htdocs/Projects/MClimate/mclimate_tool_operational.html"

with open('/data/projects/operations/GEFS_Mclimate/out/html_text.txt', mode='r') as in_file, \
     open('/data/projects/operations/GEFS_Mclimate/out/html_text2.txt', mode='r') as in_file2, \
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
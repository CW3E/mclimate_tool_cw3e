#!/usr/bin/python3
"""
Filename:    cw3e_tools.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: a collection of useful constants, colors, useful plotting and loading etc.
"""

import os
import re
import shutil
import subprocess
import glob
import xarray as xr
import pandas as pd
import datetime
import numpy as np
import cartopy.crs as ccrs
import cmocean.cm as cmo
from PIL import Image


def remove_tmp_data_files(directory, pattern):

    # Find all matching files
    files = glob.glob(os.path.join(directory, pattern))

    # Delete each file
    for file_path in files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except OSError as e:
            print(f"Error deleting {file_path}: {e}")
            
            
def plot_cw3e_logo(ax, orientation):
    ## location of CW3E logo
    if orientation == 'horizontal':
        im = '/common/CW3E_Logo_Suite/1-Horzontal-PRIMARY_LOGO/Digital/JPG-RGB/CW3E-Logo-Horizontal-FullColor-RGB.jpg'
    else:
        im = '/common/CW3E_Logo_Suite/2-Vertical/Digital/JPG-RGB/CW3E-Logo-Vertical-FullColor-RGB.jpg'
    img = np.asarray(Image.open(im))
    ax.imshow(img)
    ax.axis('off')
    return ax

def get_every_other_vector(x):
    '''
    stagger matrix setting values to diagonal
    based on https://www.w3resource.com/python-exercises/numpy/basic/numpy-basic-exercise-30.php

    Parameters
    ----------
    x : 2-D array

    Returns
    -------
    x : 2-D array
    same array as input but with the values staggered
    [[ 1.  0.  1.  0.]
     [ 0.  1.  0.  1.]
     [ 1.  0.  1.  0.]
     [ 0.  1.  0.  1.]]
    '''
    x[::2, 1::2] = 0
    x[1::2, ::2] = 0

    return x

def myround(x, base=5):
    return base * round(x/base)

def load_intermediate_GEFS(varname):
    if varname == 'freezing_level':
        varname1 = "uv"
    elif varname == 'uv1000':
        varname1 = 'freezing_level'
    ## load intermediate data
    filename_pattern = '/data/projects/operations/GEFS_Mclimate/data/tmp/tmp_GEFS_*.nc'
    ds = xr.open_mfdataset(filename_pattern, combine='nested', concat_dim='step', drop_variables=[varname1] )
    ds = ds.sortby('step')
    # Convert to hours
    ds['step'] = (ds['step'] / pd.Timedelta(hours=1)).astype(int)
    ds = ds.load()
    
    return ds

class load_GEFS_datasets:
    '''
    Loads IVT of freezing level from GEFS
    
    Parameters
    ----------
    varname : str
        variable name for forecast to compare to mclimate. 'ivt' or 'freezing_level' are acceptable
        
    fname : str
        filename you want to specify - otherwise it will use the latest IVT file from GEFS
  
    Returns
    -------
    xarray : 
        xarray dataset object with variables
    
    '''
    def __init__(self, varname, fdate=None):
        self.fpath = '/data/projects/derived_products/GEFS_IVT/data/'

        if fdate is None:          
            ## find the most recent file in the currect directory
            list_of_files = glob.glob(self.fpath+'*.nc')
            self.fname = max(list_of_files, key=os.path.getctime)
            
            # pull the initialization date from the filename
            regex = re.compile(r'\d+')
            self.date_string = regex.findall(self.fname)[1]

        if fdate is not None:
            self.date_string = fdate
    
        self.fname = self.fpath + 'GEFS_IVT_{0}.nc'.format(self.date_string)      
        self.varname = varname
        self.ensemble_name = 'GEFS'
        self.datasize_min = 15.
        self.model_init_date = datetime.datetime.strptime(self.date_string, '%Y%m%d%H')

    def calc_vars(self):
        ## load the forecast data
        ds = xr.open_dataset(self.fname) 
        ds = ds.rename({'IVT': 'ivt', 'forecast_hour': 'step'}) # need to rename this to match GEFSv12 Reforecast
        # ds = ds.drop_vars(["uIVT", "vIVT"])
        ds = ds.rename({'uIVT': 'ivtu', 'vIVT': 'ivtv'})
        ds = ds.assign_coords({"init_date": (self.model_init_date)})
        print(ds)
        # ## modifications to file regardless of variable
        # ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
        # ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(10., 70.)) ## subset to SEAK domain
        # the forecast hours available on mclimate files
        step = np.array([  6,  12,  18,  24,  30,  36,  42,  48,  54,  60,  66,  72,  78,
                84,  90,  96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156,
               162, 168])

        ds = ds.sel(step=step) # select the forecast hour steps we are interested in
        ds = ds.assign_coords({"step": (step.astype(int))}) # swap step to int
        ds = ds.mean('ensemble') # create ensemble mean

        return ds
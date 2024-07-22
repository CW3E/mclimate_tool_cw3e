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
    def __init__(self, varname, fname=None):
        path_to_data = '/data/downloaded/SCRATCH/cw3eit_scratch/'
        if varname == 'ivt':
            self.fpath = path_to_data + 'GEFS/FullFiles/'
        elif varname == 'freezing_level':
            self.fpath = path_to_data + 'GEFS/FreezingLevel/'
        
        self.varname = varname
        self.ensemble_name = 'GEFS'
        self.datasize_min = 15.

        if fname is not None:
            self.fname = fname
        if fname is None:          
            ## find the most recent file in the currect directory
            list_of_files = glob.glob(self.fpath+'*.nc')
            self.fname = max(list_of_files, key=os.path.getctime)
        
        # pull the initialization date from the filename
        regex = re.compile(r'\d+')
        date_string = regex.findall(self.fname)
        self.date_string = date_string[1]

        self.model_init_date = datetime.datetime.strptime(self.date_string, '%Y%m%d%H')

    def calc_vars(self):
        ## load the forecast data
        ds = xr.open_dataset(self.fname)
        
        if self.varname == 'ivt':
            ds = ds.rename({'IVT': 'ivt', 'forecast_hour': 'step'}) # need to rename this to match GEFSv12 Reforecast
            ds = ds.drop_vars(["uIVT", "vIVT"])
        elif self.varname == 'freezing_level':
            ds = ds.rename({'HGT_P1_L4_GLL0': 'freezing_level', 'forecast_time0': 'step', 'lat_0': 'lat', 'lon_0': 'lon', 'ensemble0': 'ensemble'}) # need to rename this to match GEFSv12 Reforecast
        
        ## modifications to file regardless of variable
        ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
        ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(10., 70.)) ## subset to SEAK domain
        # the forecast hours available on mclimate files
        step = np.array([  6,  12,  18,  24,  30,  36,  42,  48,  54,  60,  66,  72,  78,
                84,  90,  96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156,
               162, 168])

        ds = ds.sel(step=step) # select the forecast hour steps we are interested in
        ds = ds.mean('ensemble') # create ensemble mean

        return ds
    
    
class load_GFS_datasets:
    '''
    Loads IVT from GFS
    
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
        self.varname = varname
        
        self.F_lst = [  6,  12,  18,  24,  30,  36,  42,  48,  54,  60,  66,  72,
                 78, 84,  90,  96, 102, 108, 114, 120, 126, 132, 138, 144, 150,
                 156, 162, 168, 174, 180, 186, 192, 198, 204, 210, 216, 222,
                 228, 234, 240]
        
        if varname == 'ivt':
            path_to_data = '/data/downloaded/SCRATCH/cw3eit_scratch/'
            self.fpath = path_to_data + 'GFS/'

            if fdate is None:
                ## find the most recent file in the currect directory
                list_of_files = glob.glob(self.fpath+'*.nc')
                self.fname = max(list_of_files, key=os.path.getctime)

                # pull the initialization date from the filename
                regex = re.compile(r'\d+')
                self.date_string = regex.findall(self.fname)[1]
            elif fdate is not None:
                self.date_string = fdate

            fname_lst = []
            for i, F in enumerate(self.F_lst):
                fname= self.fpath + 'GFS_IVT_{0}_F{1}.nc'.format(self.date_string, F)
                fname_lst.append(fname)
            self.fname_lst = fname_lst


        elif varname == 'freezing_level':

            year = pd.Timestamp.today().year
            path_to_data = '/data/downloaded/Forecasts/GFS_025d/{0}/*'.format(year)
            if fdate is None:
                list_of_files = glob.glob(path_to_data)
                self.fpath = max(list_of_files, key=os.path.getctime)
                regex = re.compile(r'\d+')
                self.date_string = regex.findall(self.fpath)[-1]
            elif fdate is not None:
                self.date_string = fdate
            fname_lst = []
            for i, F in enumerate(self.F_lst):
                fname = '/gfs_{0}_f{1}.grb'.format(self.date_string, str(F).zfill(3))

                ## for now: copy the files to local space
                repo_path = '/home/dnash/comet_data/tmp'
                # shutil.copy(self.fpath+fname, repo_path+fname) # copy file over to data folder
                fname_lst.append(repo_path+fname)      
            self.fname_lst = fname_lst

        self.model_init_date = datetime.datetime.strptime(self.date_string, '%Y%m%d%H')

    def calc_vars(self):
        if self.varname == 'ivt':
            ## open the files with the correct forecast hour
            ds_lst = []
            for i, fname in enumerate(self.fname_lst):
                ds = xr.open_dataset(fname)
                ds = ds.rename({'lon_0': 'lon', 'lat_0': 'lat'}) # need to rename this to match GEFS
                ds_lst.append(ds)

            ## concat the dataset list into a single dataset
            ds = xr.concat(ds_lst, pd.Index(self.F_lst, name="step"))
            ## clean dataset
            ds = ds.rename({'IVT': 'ivt'}) # need to rename this to match GEFSv12 Reforecast
            ds = ds.drop_vars(["uIVT", "vIVT"])
            ds = ds.assign_coords({"init_date": (self.model_init_date)})
            ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
            ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(10., 70.)) ## subset to SEAK domain
            
            
        if self.varname == 'freezing_level':
            ## open the files with the correct forecast hour
            ds_lst = []
            for i, fname in enumerate(self.fname_lst):
                ds = xr.open_dataset(fname, engine='cfgrib', filter_by_keys={'typeOfLevel': 'isothermZero'})
                ds = ds.rename({'longitude': 'lon', 'latitude': 'lat', 'time': 'init_date',
                                'gh': 'freezing_level'}) # need to rename this to match GEFS
                ds_lst.append(ds)

            ## concat the dataset list into a single dataset
            ds = xr.concat(ds_lst, dim="step")
            ds = ds.drop_vars(["r"])
            ds = ds.assign_coords({"step": (self.F_lst)})
            ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
            ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.)) ## subset to SEAK domain

        return ds
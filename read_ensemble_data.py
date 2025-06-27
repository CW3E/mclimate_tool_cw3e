#!/usr/bin/python3
"""
Filename:    read_ensemble_data.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: functions to read ensemble grb data from GEFS
"""

import sys
import os
import glob
import shutil
import subprocess
import re
import xarray as xr
import numpy as np
import pandas as pd
import datetime

def read_gefs_ensemble(filename, vardict, show_catalog=False):

    '''
    function usage: read selected variables from GEFS .grb2 data 

    filename example:
    gefs_2024111212_F006.grb2

    vardict example:
    vardict = {
            "freezing_level": {'dataType': 'pf', 'typeOfLevel': 'isothermZero', 'shortName': 'gh'},
            "u_wind":{'dataType': 'pf', "typeOfLevel":'isobaricInhPa',"shortName":"u"},
            "v_wind":{'dataType': 'pf', "typeOfLevel":'isobaricInhPa',"shortName":"v"}
        }
    
    Output:
    Dictionary of objects for each variable set in the vardict argument. Ex.
    uwind = selected_vars["u_wind"].values
    uwind_latitude = selected_vars["u_wind"].latitude.values
    uwind_longitude = selected_vars["u_wind"].longitude.values

    for 3d variables:
    uwind_pressure_levels = selected_vars["u_wind"].isobaricInhPa.values

    '''
    selected_vars = {}
    #iterating over all variables in the vardict and storing each one in a new dictionary called selected_vars
    for var in vardict.keys():

        ds = xr.open_dataset(filename,
                        engine='cfgrib',filter_by_keys=vardict[var],backend_kwargs={"indexpath": ''})
        
        
        #exceptions when shortName does not match variable name in the grib
        if var == 'u_wind_10m':
            selected_vars[var] = ds["u10"]
        elif var == 'v_wind_10m':
            selected_vars[var] = ds["v10"]
        else:    
            selected_vars[var] = ds[vardict[var]["shortName"]]    

    return selected_vars

class load_GEFS_datasets:
    '''
    Loads variables needed for ivt cross section plots from GEFS .grb2 files
    
    Parameters
    ----------
    F : int
        the forecast lead requested
        
    fdate : str
        string of date for the filename in YYYYMMDDHH format
  
    Returns
    -------
    xarray : 
        xarray dataset object with variables
    
    '''
    def __init__(self, F=None, fdate=None):
        print('Preprocessing {0} ...'.format(F))
        self.F = F
        path_to_data = '/data/projects/external_datasets/GEFS/processed/*/'
        if fdate is None:
            list_of_files = glob.glob(path_to_data)
            self.fpath = max(list_of_files, key=os.path.getctime)
            regex = re.compile(r'\d+')
            self.date_string = regex.findall(self.fpath)[-1]
        elif fdate is not None:
            self.date_string = fdate
            self.fpath = '/data/projects/external_datasets/GEFS/processed/{0}/'.format(self.date_string)
        fname = 'gefs_{0}_F{1}.grb2'.format(self.date_string, str(self.F).zfill(3))
        self.fname = self.fpath+fname

    def calc_vars(self):
        ## dictionary of variables we need for the cross section
        gefs_vardict = {"freezing_level": {'dataType': 'pf', 'typeOfLevel': 'isothermZero', 'shortName': 'gh'}, ## freezing level
                        "u_wind":{'dataType': 'pf', "typeOfLevel":'isobaricInhPa',"shortName":"u"}, #U-component of wind
                        "v_wind":{'dataType': 'pf', "typeOfLevel":'isobaricInhPa',"shortName":"v"}, #V-component of wind
                       }
        
        #gefs is a dictionary of datasets
        gefs = read_gefs_ensemble(filename=self.fname,vardict=gefs_vardict, show_catalog=False)
        
        # BUILD DATASET
        ## get freezing level
        freezing_level_da = gefs['freezing_level']
        u_wind_da = gefs['u_wind'].sel(isobaricInhPa=1000)
        v_wind_da = gefs['v_wind'].sel(isobaricInhPa=1000)
        
        ds = xr.merge([freezing_level_da, u_wind_da, v_wind_da])
        
        ds = ds.rename({'gh': 'freezing_level', 'latitude': 'lat', 'longitude': 'lon', 'time': 'init_date'}) # need to rename this to match GEFSv12 Reforecast
        ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
        ds = ds.sortby('lon')
        ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.)) ## subset to mclimate domain
        
        ## compute uv magnitude
        uv = np.sqrt(ds.u**2 + ds.v**2)
        ds = ds.assign(uv=(['number', 'lat','lon'],uv.data))
        # ds = ds.drop_vars(["u", "v"])
        
        ## compute ensemble mean
        ds = ds.mean('number')
        
        ## write intermediate data files
        print('...Writing {0} lead to intermediate nc file'.format(self.F))
        out_fname = '/data/projects/operations/GEFS_Mclimate/data/tmp/tmp_GEFS_{0}.nc'.format(self.F)
        ds.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')
        ds.close() ## close data

        return None

    
    def calc_qpf(self):
        
        gefs_vardict = {"prec":{'dataType': 'cf', 'name': 'Total Precipitation', 'typeOfLevel': 'surface', 'level': 0, 'paramId': 228228, 'shortName': 'tp'} #total precipitation
                       }
        
        ## Read QPF data for all time steps
        print("Reading grb files for qpf...")
        ds_lst = []
        for i, F in enumerate(np.arange(3, 169, 3)):
            fname_qpf = self.fpath + 'gefs_{0}_F{1}.grb2'.format(self.date_string, str(F).zfill(3))
            dsa = xr.open_dataset(fname_qpf, engine='cfgrib',filter_by_keys=gefs_vardict['prec'])
            dsa = dsa.expand_dims(dim='step')
            print(dsa)
            ds_lst.append(dsa)

        ds = xr.concat(ds_lst, dim='step')

        ## fix lons 
        ds = ds.assign_coords({"longitude": (((ds.longitude + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
        ## subset to N. America [0, 70, 180, 295]
        ds = ds.sel(latitude=slice(70, 0), longitude=slice(-179.5, -60.))
        
        ## run preprocess
        print("Preprocessing precipitation...")
        ## convert precipitation to mm per hour
        ts_3hr = pd.timedelta_range(start='0 day', periods=57, freq='3H')
        ts_6hr = pd.timedelta_range(start='0 day', periods=29, freq='6H')
        tp = ds.tp ## pull out tp
        prec_3hr = tp.sel(step=ts_3hr[1::2]) ## grab only the 3hr values
        tp2 = tp.diff(dim='step') ## calculate difference in precip
        ## the values for 6hr timesteps are correct, the values for 3hr timesteps are incorrect
        prec_6hr = tp2.sel(step=ts_6hr[1:]) # grab only the 6hr values
        new_prec = prec_3hr.combine_first(prec_6hr) # combine the correct 3hr values with the correct 6hr values
        ds = ds.drop_vars(["tp"]) # get rid of old tp (accumulated variable)
        ds = xr.merge([ds, new_prec]) # merge dataset with new tp
        
        ## compute ensemble mean
        print(ds)
        ds = ds.mean('number')
        print("Saving QPF as netcdf...")
        ## save as netCDF
        ## save data to netCDF file
        print('Writing {0} to netCDF ....'.format('qpf'))
        path_to_out = '/data/projects/operations/GEFS_Mclimate/data/tmp/'
        out_fname = 'QPF.t00z.0p50.f003-f168.tmp'
        ds.to_netcdf(path=path_to_out + out_fname, mode = 'w', format='NETCDF4')
        ds.close() ## close data
        
        return None

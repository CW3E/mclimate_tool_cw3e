"""
Filename:    mclimate_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for comparing GEFSv12 mClimate to GEFSv12 reforecast
"""

import os, sys
import xarray as xr
import numpy as np
import pandas as pd

import cw3e_tools as ctools

def compare_mclimate_to_forecast(fc, mclimate, varname):
    if varname == 'uv1000':
        varname = 'uv'
    ## compare IVT forecast to mclimate
    b_lst = []
    quant_lst = [0.  , 0.75, 0.9 , 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.  ]
    nquantiles = len(quant_lst)
    for i, quant in enumerate(range(nquantiles)):
        bottom = mclimate[varname].isel(quantile=quant) # minimum threshold
        
        if i == 0:
            # only need to see where variable in the forecast is less than minimum quantile
            b = xr.where(cond=fc[varname] < bottom, x=quant_lst[i], y=np.nan)          
            
        elif (i > 0) & (i < nquantiles-1):
            # where IVT in the forecast is greater than current quartile, but less than next quartile
            top = mclimate[varname].isel(quantile=i+1)
            b = xr.where(cond=(fc[varname] > bottom) & (fc[varname] < top), x=quant_lst[i], y=np.nan)
            b = b.assign_coords({'quantile': (quant_lst[i])})
            
        elif (i == nquantiles-1):
            # where variable is greater than final quartile
            b = xr.where(cond=(fc[varname] > bottom), x=quant_lst[i], y=np.nan)
            b = b.expand_dims(dim="quantile")
    
        b.name = varname
        var_dict = {'mclimate': (['step', 'lat', 'lon'], b.squeeze().values)}
        new_ds = xr.Dataset(var_dict,
                        coords={'lat': (['lat'], b.lat.values),
                                'lon': (['lon'], b.lon.values),
                                'step': (['step'], b.step.values)})     
        b_lst.append(new_ds)
        
    ds = xr.merge(b_lst)
    ds = ds.assign_coords({"init_date": (fc.init_date)})

    return ds

def load_reforecast(date, varname):
    path_to_data = '/expanse/nfs/cw3e/cwp140/' 
    fname_pattern = path_to_data + 'preprocessed/GEFSv12_reforecast/{0}/{1}_{0}_F*.nc'.format(varname, date)
    forecast = xr.open_mfdataset(fname_pattern, engine='netcdf4', concat_dim="step", combine='nested')
    forecast  = forecast.sortby("step") # sort by step (forecast lead)
    tmp = forecast.step[1::2].values
    forecast = forecast.sel(step=tmp) ## select every 6 hours up to 10 days lead time
    step_vals = forecast.step.values / pd.Timedelta(hours=1)
    forecast = forecast.assign_coords({"step": step_vals.astype(int)})
    if varname == 'ivt':
        forecast = forecast.rename({'longitude': 'lon', 'latitude': 'lat', 'time': 'init_date'}) # need to rename this to match GEFSv12 Reforecast mclimate
        forecast = forecast.drop_vars(["ivtu", "ivtv"])
    elif varname == 'uv1000':
        forecast = forecast.rename({'longitude': 'lon', 'latitude': 'lat'}) # need to rename this to match GEFSv12 Reforecast
        uv = np.sqrt(forecast.u**2 + forecast.v**2)
        forecast = forecast.assign(uv=(['number', 'step', 'lat','lon'],uv.data))
        forecast = forecast.drop_vars(["u", "v"])
        forecast = forecast.assign_coords(init_date=(pd.to_datetime(date)))
    else:
        forecast = forecast.assign_coords(init_date=(pd.to_datetime(date)))
        
    
    forecast = forecast.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.))
    forecast = forecast.mean('number') # ensemble mean
    forecast = forecast.load()

    return forecast

def load_mclimate(mon, day, varname, server):
    if varname == 'UV1000':
        varname == 'uv1000'
    ## special circumstance for leap day
    if (mon == '02') & (day == '29'):
        mon = '02'
        day = '28'
        
    ## load mclimate data
    if server == 'skyriver':
        path_to_data = '/home/dnash/comet_data/' # skyriver
    elif server == 'expanse':
        path_to_data = '/expanse/nfs/cw3e/cwp140/' # expanse 
    fname = path_to_data + 'preprocessed/{2}_mclimate/GEFSv12_reforecast_mclimate_{2}_{0}{1}.nc'.format(mon, day, varname)
    # print(fname_pattern)
    ds = xr.open_dataset(fname)
    # ds = ds.sortby("step") # sort by step (forecast lead)
    if (varname == 'ivt') | (varname == 'uv1000'):
        ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'}) # need to rename this to match GEFSv12 Reforecast
    else:
        ds = ds
    ds = ds.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.))
    ## load the data into memory
    ds = ds.load()

    return ds

def load_archive_GEFS_forecast(date, varname):
    ### load forecast from GEFS
    if varname == 'ivt':
        varname = 'IVT'
    elif varname == 'uv1000':
        varname = 'UV1000'
    
    fname_pattern = '/expanse/nfs/cw3e/cwp140/preprocessed/GEFS/GEFS/{0}.t00z.0p50.f*.{1}'.format(date, varname)
    forecast = xr.open_mfdataset(fname_pattern, engine='netcdf4', concat_dim="step", combine='nested')
    forecast = forecast.rename({'longitude': 'lon', 'latitude': 'lat', 
                                  "time": "init_date"}) # need to rename this to match GEFSv12 Reforecast
    
    if varname == 'freezing_level':
        forecast = forecast.rename({"gh": "freezing_level"})
    if varname == 'UV1000':
        uv = np.sqrt(forecast.u**2 + forecast.v**2)
        forecast = forecast.assign(uv=(['step', 'lat','lon'],uv.data))
        forecast = forecast.drop_vars(["u", "v"])
        
    forecast = forecast.assign_coords({"lon": (((forecast.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
    s = forecast.step.values
    step_hours = s / np.timedelta64(1, 'h')
    forecast = forecast.assign_coords({"step": (step_hours.astype(int))}) # swap step to int
    forecast = forecast.sel(lon=slice(-179.5, -110.), lat=slice(70., 10.))
    forecast = forecast.load()

    return forecast

def run_compare_mclimate_forecast(varname, fdate, model, server):
    ## load forecast data
    if model == 'GEFSv12_reforecast':
        forecast = load_reforecast(fdate, varname)

    elif model == 'GFS':
        ## using operational GFS data
        s = ctools.load_GFS_datasets(varname, fdate) ## need to set date to what I have copied to personal dir
        forecast = s.calc_vars()

    elif model == 'GEFS':
        ## using operational GEFS data
        s = ctools.load_GEFS_datasets(varname, fdate)
        forecast = s.calc_vars()

    elif model == 'GEFS_archive':
        forecast = load_archive_GEFS_forecast(fdate, varname)
    
    ## get month and date from the intialization date of the forecast
    ts = pd.to_datetime(forecast.init_date.values, format="%Y%m%d%H")
    mon = ts.strftime('%m')
    day = ts.strftime('%d')
    print(mon, day)
    
    ## load mclimate data based on the initialization date
    mclimate = load_mclimate(mon, day, varname, server)

    if (model == 'GEFS') | (model == 'GEFS_archive'):
        ## regrid/interpolate data to all have same grid size
        regrid_lats = forecast.lat
        regrid_lons = forecast.lon
        mclimate = mclimate.interp(lon=regrid_lons, lat=regrid_lats)
    
    ## compare the mclimate to the reforecast
    ds = compare_mclimate_to_forecast(forecast, mclimate, varname)

    return forecast, ds
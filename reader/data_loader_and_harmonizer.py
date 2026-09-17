"""
Filename:    data_loader_and_harmonizer.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading forecast data (GEFSv12 Reforecast, GEFS Archive, or GEFS operational) and the associated M-Climate data
Also cleans up and aligns forecast and mclimate so they are directly comparable.
"""

import pandas as pd
import os
import xarray as xr
import numpy as np

from config import DOY_BLOCKS
from utils import globalvars
from reader import gefs_realtime

def convert_leadtime_to_integer_hours(ds):
    
    if np.issubdtype(ds.lead_time.dtype, np.timedelta64):
        ds = ds.assign_coords(
            lead_time=ds.lead_time / np.timedelta64(1, "h")
        )
    
    ds = ds.assign_coords(
        lead_time=ds.lead_time.astype(int)
    )

    print(ds)

    return ds

def clean_datetime_attrs(ds):
    for coord in ["init_date", "valid_time"]:
        if coord in ds.coords:
            ds[coord].attrs.pop("units", None)
            ds[coord].attrs.pop("calendar", None)

    return ds

def subset_domain(ds, domain):

    lat = ds.latitude

    # handle ascending vs descending latitude
    if lat[0] > lat[-1]:
        lat_slice = slice(domain["lat_max"], domain["lat_min"])
    else:
        lat_slice = slice(domain["lat_min"], domain["lat_max"])

    return ds.sel(
        longitude=slice(domain["lon_min"], domain["lon_max"]),
        latitude=lat_slice,
    ).sortby('latitude')

def standardize_coords(ds):

    coord_map = {
        "lat": "latitude",
        "lon": "longitude",
        "step": "lead_time",
        "time": "init_date",
        "forecast_hour": "lead_time",
        "ensemble": "number",
    }

    var_map = {
        "tp": "qpf",
        "gh": "freezing_level",
        "IVT": "ivt",
        "uIVT": "ivtu",
        "vIVT": "ivtv",
    }

    coord_rename = {
        k: v
        for k, v in coord_map.items()
        if k in ds.coords or k in ds.dims
    }

    var_rename = {
        k: v
        for k, v in var_map.items()
        if k in ds.data_vars
    }

    return ds.rename(
        coord_rename | var_rename
    )

def longitude_normalizer(ds):
    # -------------------------------------------------
    # Longitude normalization
    # -------------------------------------------------

    if "longitude" not in ds.coords:
        return ds

    lon_min = ds.longitude.min().item()
    lon_max = ds.longitude.max().item()

    # Only normalize if longitudes are in the 0-360 convention
    if lon_min >= 0 and lon_max > 180:
        ds = ds.assign_coords(
            longitude=((ds.longitude + 180) % 360) - 180
        )
        ds = ds.sortby("longitude")

    return ds

def harmonize_datasets(
    forecast,
    mclimate,
    varname,
    ensemble_mean=True,
    domain=None,
):
    """
    Harmonize forecast and mclimate datasets
    so they are directly comparable.
    """
    print('Harmonizing forecast and mclimate datasets')
    # -------------------------------------------------
    # 1. Rename coordinates
    # -------------------------------------------------

    forecast = standardize_coords(forecast)
    mclimate = standardize_coords(mclimate)

    # -------------------------------------------------
    # 2. Convert lon from 0-360 to -180 to 180
    # -------------------------------------------------

    forecast = longitude_normalizer(forecast)
    mclimate = longitude_normalizer(mclimate)

    # -------------------------------------------------
    # 2. Spatial subset
    # -------------------------------------------------

    forecast = subset_domain(forecast, domain)
    mclimate = subset_domain(mclimate, domain)

    # -------------------------------------------------
    # 3. Ensemble mean
    # -------------------------------------------------

    if ensemble_mean and "number" in forecast.dims:
        forecast = forecast.mean("number")

    # -------------------------------------------------
    # 4. Rename vars
    # -------------------------------------------------
    mclimate = mclimate.rename({f"{varname}_percentiles": varname})


    # -------------------------------------------------
    # 5. Convert lead times to integer hours
    # -------------------------------------------------

    if np.issubdtype(forecast.lead_time.dtype, np.timedelta64):

        lead_hours = (
            forecast.lead_time.values
            / np.timedelta64(1, "h")
        ).astype(int)

        forecast = forecast.assign_coords(
            lead_time=lead_hours
        )

    # -------------------------------------------------
    # 6. Match lead times
    # -------------------------------------------------

    common_leads = np.intersect1d(
        forecast.lead_time,
        mclimate.lead_time,
    )

    forecast = forecast.sel(lead_time=common_leads)
    mclimate = mclimate.sel(lead_time=common_leads)

    # -------------------------------------------------
    # 7. Regrid if needed
    # -------------------------------------------------

    if (
        not forecast.latitude.equals(mclimate.latitude)
        or not forecast.longitude.equals(mclimate.longitude)
    ):

        forecast = forecast.interp(
            latitude=mclimate.latitude,
            longitude=mclimate.longitude,
        )

    # -------------------------------------------------
    # 8. Standard dimension ordering
    # -------------------------------------------------

    preferred_order = [
        "number",
        "ensemble",
        "init_date",
        "lead_time",
        "latitude",
        "longitude",
    ]
    
    dim_order = [
        d for d in preferred_order
        if d in forecast.dims
    ]
    
    forecast = forecast.transpose(*dim_order)

    # -------------------------------------------------
    # 9. Remove time-encoding attributes 
    # -------------------------------------------------

    forecast = clean_datetime_attrs(forecast)
    mclimate = clean_datetime_attrs(mclimate)

    # -------------------------------------------------
    # 10. Convert lead_time to integer hours
    # -------------------------------------------------
    
    forecast = convert_leadtime_to_integer_hours(forecast)
    mclimate = convert_leadtime_to_integer_hours(mclimate)

    return forecast, mclimate

def load_reforecast(init_date, varname):

    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    filename = os.path.join(
        globalvars.path_to_data,
        "preprocessed/GEFSv12_reforecast",
        f"{varname}_final",
        f"GEFSv12_reforecast_{varname}_{init_date:%Y%m%d}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_gefs_archive(init_date, varname):

    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    filename = os.path.join(
        globalvars.path_to_data,
        "preprocessed/GEFS",
        f"{varname}",
        f"{init_date:%Y%m%d}_{varname}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_gefs_realtime(init_date, varname):

    if varname == "freezing_level":
        return gefs_realtime.load_realtime_freezing_level(init_date)

    elif varname == "uv":
        return gefs_realtime.load_realtime_uv(init_date)

    elif varname == "qpf":
        return gefs_realtime.load_realtime_qpf(init_date)

    elif varname == "ivt":
        return gefs_realtime.load_realtime_ivt(init_date)

    else:
        raise ValueError(f"Unsupported realtime variable: {varname}")

def load_mclimate(init_date, varname, doy_blocks, base_dir=None):
    """
    Load model climatology dataset based on init_date and DOY blocks.

    Parameters
    ----------
    init_date : str, int, or datetime-like
        Initialization date (e.g., '20000115', 20000115, or datetime)
    varname : str
        Variable name (e.g., 'ivt')
    doy_blocks : dict
        Dictionary of DOY blocks (e.g., DOY_BLOCKS)
    base_dir : str, optional
        Base data directory

    Returns
    -------
    xarray.Dataset
    """

    if base_dir is None:
        base_dir = globalvars.path_to_data

    # Convert to datetime
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")
    doy = init_date.dayofyear

    # Handle leap year edge case (optional but recommended)
    if doy == 366:
        doy = 365

    # Find matching DOY block
    block_name = None
    for block in doy_blocks.values():
        if block["doy_min"] <= doy <= block["doy_max"]:
            block_name = block["name"]
            break

    if block_name is None:
        raise ValueError(f"No DOY block found for DOY={doy}")

    # Build filename
    filename = os.path.join(
        base_dir,
        f"preprocessed/mclimate_2.0/{varname}/concat_DOY",
        f"mclimate_{varname}_{block_name}.nc"
    )

    print(f"Loading DOY={doy} → {block_name}")
    print(filename)

    ds = xr.open_dataset(filename)
    ds = ds.sel(doy=doy)

    return ds

def prepare_forecast_and_mclimate(
    init_date,
    varname,
    domain,
    source="reforecast",
):

    if source == "reforecast":
        forecast = load_reforecast(
            init_date,
            varname,
        )

    elif source == "archive":
        forecast = load_gefs_archive(
            init_date,
            varname,
        )

    elif source == "realtime":
        forecast = load_gefs_realtime(
            init_date,
            varname,
        )

    else:
        raise ValueError(
            f"Unsupported forecast source: {source}"
        )

    mclimate = load_mclimate(
        init_date,
        varname,
        DOY_BLOCKS,
    )

    forecast, mclimate = harmonize_datasets(
        forecast=forecast,
        mclimate=mclimate,
        varname=varname,
        domain=domain,
    )

    return forecast, mclimate
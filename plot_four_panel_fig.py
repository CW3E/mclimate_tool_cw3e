"""
Filename:    plotter.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading GEFS_reforecast, GEFS_archive, or GEFS_operational data, comparing to mclimate, then creating a four panel map with Mclimate ranks and a heatmap with maximum Mclimate rank within Southeast Alaska.
"""

## import libraries
import os, sys
import yaml
import xarray as xr
import pandas as pd
import numpy as np
from datetime import timedelta
import glob
import itertools

# plotting
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
from matplotlib.gridspec import GridSpec
from matplotlib.colorbar import Colorbar # different way to handle colorbar
import textwrap
import matplotlib as mpl
mpl.use('agg')

import custom_cmaps as ccmap
from plotter import plot_mclimate_forecast_four_panel
import mclimate_funcs as mclim_func

def compute_AR_duration_AR_impact_index(ds3):
    ## compute duration of IVT >= 95th percentile
    AR = xr.where(ds3.ivt >= 0.95, 1, 0)
    a = AR != 0 # this will place True for all rows where AR is not 0
    
    # get the temporal resolution in hours
    t = ds3['step'].isel(step=1) - ds3['step'].isel(step=0) 
    nhrs = t.values.astype('timedelta64[h]') # convert to hours
    
    ## this grabs the start and stop indices of each AR
    tmp = a.cumsum(dim='step')-a.cumsum(dim='step').where(~a).ffill(dim='step').fillna(0).astype(int) # cumulative sum where not 0
    duration = tmp*nhrs.astype(int)
    duration = duration.rename("duration")
    ds3 = xr.merge([ds3, duration])

    ## calculate index score
    ## +1 Index Point for IVT >= 95th percentile
    AR1 = xr.where(ds3.ivt >= 0.95, 1, 0)
    
    ## +1 Index Point for freezing_level >= 95th percentile
    AR2 = xr.where(ds3.freezing_level >= 0.95, 1, 0)
    
    ## +1 Index Point for uv1000 >= 95th percentile
    AR3 = xr.where(ds3.uv >= 0.95, 1, 0)
    
    ## +1 Index Point for duration >= 24
    AR4 = xr.where(ds3.duration >= 24, 1, 0)
    
    ## +1 Index Point for duration >= 48
    AR5 = xr.where(ds3.duration >= 48, 1, 0)
    
    AR_index = AR1 + AR2 + AR3 + AR4 + AR5
    
    AR_index = AR_index.rename("AR_index")
    ds3 = xr.merge([ds3, AR_index])

    return ds3

def create_dataframe_max_values(ds3):
    ## create table with max value within extent
    ext=[-141., -130., 54., 60.]
    tmp = ds3.sel(lat=slice(ext[2], ext[3]), lon=slice(ext[0], ext[1]))
    maxval = tmp.max(dim=['lat', 'lon']).fillna(0)
    
    
    df = maxval.to_dataframe()
    df = df.drop(['init_date'], axis=1)
    df['ivt'] = df['ivt']*100
    df['freezing_level'] = df['freezing_level']*100
    df['uv'] = df['uv']*100
    df = df.rename(columns={"ivt": "IVT", "freezing_level": "Freezing Level", "uv": "UV", "duration": "Duration"})
    
    ## create list of valid dates
    ts = pd.to_datetime(ds3.init_date.values, format="%Y%m%d%H")
    # ts = ds.init_date.values
    init_date = ts.strftime('%Y%m%d%H')
    init_time = ts.strftime('Initialized: %HZ %d %b %Y')
    col2 = []
    date_lbl = []
    step_lst = ds3.step.values.tolist()
    for i, step in enumerate(step_lst):
        ts_valid = ts + timedelta(hours=step)
        HH = ts_valid.strftime('%H')
        if HH == '06':
            date_lbl.append(ts_valid.strftime('%b %d'))
        valid_str = ts_valid.strftime('%H UTC')
        txt = '{0} | F{1}'.format(valid_str, str(step).zfill(3))
        col2.append(txt)
        
    df.index = col2

    return df, init_time, date_lbl
    
def create_heatmap_annotation_labels(data):
    ## make custom annotation labels
    ## if value < 75, label is '<75'
    ## if value > 99, label is 'MAX'
    
    lbl_lst = []
    for i, d in enumerate(data):
        if d[0] < 75.:
            lbl = '<75'
        elif d[0] > 99.:
            lbl = 'MAX'
        else:
            lbl = "{:.0f}".format(d[0])
        lbl_lst.append(lbl)

    lbl_lst = np.asarray(lbl_lst).reshape(data.shape[0],1)
    
    return lbl_lst

def create_mini_heatmap(ax, df, cmap_name, varname, ytcklbl, xtcklbl):
    
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
    data_len = df[varname].shape
    data = np.asarray(df[varname]).reshape(data_len[0],1)
    if varname != 'Duration':
        data_lbls = create_heatmap_annotation_labels(data)
    else:
        data_lbls = True
        
    sns.heatmap(data, cbar=False, annot=data_lbls, cmap=cmap, norm=norm, linewidths=.5, ax=ax, 
                yticklabels=ytcklbl, xticklabels=[xtcklbl], fmt='')
    ax.xaxis.tick_top()
    ax.set(xlabel="", ylabel="")
    ax.hlines([3, 7, 11, 15, 19, 23, 27, 31, 35, 39], color='k', lw=0.8, *ax.get_xlim())
    plt.yticks(rotation=0)

    return ax

def plot_heatmap(df, init_time, date_lbl, fdate, fname):

    plot_dict = {
                  "IVT" : {
                    "cmap_name" : "mclimate_green",
                    "ytcklbl" : df.index.values,
                    "xtcklbl" : 'IVT'
                  },
                  "Freezing Level" : {
                    "cmap_name" : "mclimate_red",
                    "ytcklbl" : False,
                    "xtcklbl" : 'Z0'
                  },
                  "UV" : {
                    "cmap_name" : "mclimate_purple",
                    "ytcklbl" : False,
                    "xtcklbl" : 'UV'
                  },
                  "Duration" : {
                    "cmap_name" : "duration",
                    "ytcklbl" : False,
                    "xtcklbl" : 'DUR'
                  },
                }
    ext=[-141., -130., 54., 60.]
    fmt = 'png'
    fig = plt.figure()
    fig.set_size_inches((2.0,10.0))
    fig.dpi = 300
    
    nrows = 2
    ncols = 4
    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, height_ratios=[1, 0.05], width_ratios = [1, 1, 1, 1], wspace=0.05, hspace=0.05)
    ## use gs[rows index, columns index] to access grids
    
    ## loop through each heatmap
    varname_lst = ['IVT', 'Freezing Level', 'UV', 'Duration']
    for i, varname in enumerate(varname_lst):
        print(varname)
        ax = fig.add_subplot(gs[0, i])
        
        create_mini_heatmap(ax, df, plot_dict[varname]['cmap_name'], varname, 
                            plot_dict[varname]['ytcklbl'], plot_dict[varname]['xtcklbl'])
        if i == 0:
            ax.set_title(init_time, fontsize=11, loc='left')
    
            lbl_loc = [1, 4.5, 8.5, 12.5, 16.5, 20.5, 24.5, 28.5, 32.5, 36.5]
            for j, datel in enumerate(date_lbl):
                ## add month day labels
                kw = {'weight': 'bold', 'size': 9}
                ax.text(-3.25, lbl_loc[j]+1.25, textwrap.fill(datel, width=3), va='bottom', ha='center',
                    rotation='horizontal', rotation_mode='anchor', **kw)
    
    
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    domain = u"{:.0f}\N{DEGREE SIGN}N to {:.0f}\N{DEGREE SIGN}N, {:.0f}\N{DEGREE SIGN}W to {:.0f}\N{DEGREE SIGN}W".format(ext[2], ext[3], ext[0], ext[1])
    txt = 'Maximum percentile rank (xth) within {0}'.format(domain)
    ann_ax = fig.add_subplot(gs[-1, :])
    ann_ax.axis('off')
    ann_ax.annotate(textwrap.fill(txt, 40), # this is the text
                (0, 0.), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(-80,20), # distance from text to points (x,y)
                ha='left', # horizontal alignment can be left, right or center
                **kw_ticklabels)
    
    # Save the figure
    fig.savefig('%s.%s' % (fname, fmt), bbox_inches='tight', dpi=fig.dpi)
    
def output_compare_mclimate_to_reforecast(fdate, model, impact_date=None):
    if impact_date == None:
        fig_path = '/expanse/nfs/cw3e/cwp140/images_operational/mclimate_{0}/'.format(fdate)
    else: 
        fig_path = '/expanse/nfs/cw3e/cwp140/images_historical/{1}/mclimate_{0}/'.format(fdate, impact_date)
    
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    
    ####################################
    ### COMPARE FORECAST TO MCLIMATE ###
    ####################################
    print(' ...... running Mclimate comparison ...')
    var_lst = ['ivt', 'freezing_level', 'uv1000']
    ds_lst = []
    ds_lst2 = []
    fc_lst = []
    for i, varname in enumerate(var_lst):
        forecast, ds = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='expanse')
        fc_lst.append(forecast)
        ds_lst.append(ds)
    
        if varname == 'uv1000':
                ds = ds.rename({'mclimate': 'uv'})
        else:
            ds = ds.rename({'mclimate': varname})
        ds_lst2.append(ds)
        
    ### merge the datasets
    ds3 = xr.merge(ds_lst2)
    ds3 = ds3.sortby('lat')
    
    fc = xr.merge(fc_lst)
    fc = fc.sortby('lat')

    ## compute AR duration and AR Impact Index value
    ds3 = compute_AR_duration_AR_impact_index(ds3)

    ####################
    ### CREATE PLOTS ###
    ####################
    print(' ...... creating four panel plot ...')
    step_lst = ds3.step.values
    for i, step in enumerate(step_lst):
        print(step)
        out_fname = fig_path + 'SEAK_mclimate_F{0}'.format(step)
        plot_mclimate_forecast_four_panel(ds3, fc, step, out_fname, domain="SEAK")
        out_fname = fig_path + 'NPAC_mclimate_F{0}'.format(step)
        plot_mclimate_forecast_four_panel(ds3, fc, step, out_fname, domain="NPAC")

    ## create dataframe with max values
    print(' ...... creating dataframe with maximum values ...')
    df, init_time, date_lbl = create_dataframe_max_values(ds3)

    ## save as csv
    if impact_date is not None:
        fname = '/expanse/nfs/cw3e/cwp140/images_historical/{1}/mclimate_init{0}.csv'.format(fdate, impact_date)
        df.to_csv(fname, index=True)

    ######################
    ### CREATE HEATMAP ###
    ######################
    print(' ...... creating heatmap ...')
    out_fname = fig_path + 'heatmap'
    plot_heatmap(df, init_time, date_lbl, fdate, out_fname)
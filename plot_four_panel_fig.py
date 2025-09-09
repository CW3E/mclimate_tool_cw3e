"""
Filename:    plot_four_panel_fig.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for creating a four panel map with Mclimate ranks and a heatmap with maximum Mclimate rank within Southeast Alaska.
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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import gc

# plotting
import seaborn as sns
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
from matplotlib.gridspec import GridSpec
from matplotlib.colorbar import Colorbar # different way to handle colorbar
import textwrap

import custom_cmaps as ccmap
from plotter import draw_basemap, set_cw3e_font
import mclimate_funcs as mclim_func
import globalvars

path_to_data = globalvars.path_to_data

def compute_ivt_uv_direction_relative_to_slope(forecast, fdate, server='expanse'):
    ## read slope_aspect netCDF
    if server == 'expanse':
        fname = f"/dev/shm/GEFSv12_slope_aspect_{fdate}.nc"
        
    else:
        fname = '/data/projects/operations/GEFS_Mclimate/data/GEFSv12_slope_aspect.nc'
    aspect = xr.open_dataset(fname)

    ## calculate different in direction of ivt and uv and aspect
    ivtdir_diff = (forecast.ivtdir-aspect.aspect) % 360
    uvdir_diff = (forecast.uvdir-aspect.aspect) % 360
    aspect.close()
    del aspect 

    return ivtdir_diff, uvdir_diff
    
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
    ## +0.5 Index Point for IVT >= 95th percentile
    AR1 = xr.where(ds3.ivt >= 0.95, 0.5, 0)

    ## check if init date is between Oct 15 and May 1
    ## if yes, then a point can be assigned
    da = ds3.init_date
    cond = ( (da.dt.month > 10) | ((da.dt.month == 10) & (da.dt.day > 15)) ) | (da.dt.month < 5)
    if cond == True:
        ## +1 Index Point for freezing_level >= 95th percentile
        AR2 = xr.where(ds3.freezing_level >= 0.95, 1, 0)
    else:
        AR2 = xr.where(ds3.freezing_level >= 0.95, 0, 0)
    
    ## +0.5 Index Point for uv1000 >= 95th percentile
    AR3 = xr.where(ds3.uv >= 0.95, 0.5, 0)
    
    ## +0.5 Index Point for duration >= 24
    AR4 = xr.where(ds3.duration >= 24, 0.5, 0)
    
    ## +0.5 Index Point for duration >= 48
    AR5 = xr.where(ds3.duration >= 48, 0.5, 0)

    ## +0.5 Index Point for IVT direction within 60 degrees of aspect
    da = ds3.ivtdir_diff
    mask = ((da >= 0) & (da <= 30)) | ((da >= 330) & (da <= 360)) | ((da >= 150) & (da <= 210))
    AR6 = xr.where(mask, 0.5, 0.0) 

    ## +0.5 Index Point for uv1000 direction within 60 degrees of aspect
    da = ds3.uvdir_diff
    mask = ((da >= 0) & (da <= 30)) | ((da >= 330) & (da <= 360)) | ((da >= 150) & (da <= 210))
    AR7 = xr.where(mask, 0.5, 0.0) 

    ## +0.5 Index Point for QPF >= 95th percentile
    AR8 = xr.where(ds3.qpf >= 0.95, 0.5, 0)

    ## +0.5 Index Point for QPF >= 98th percentile
    AR9 = xr.where(ds3.qpf >= 0.98, 0.5, 0)
    
    # AR_index = AR1 + AR2 + AR3 + AR4 + AR5
    AR_index = AR1 + AR2 + AR3 + AR4 + AR5 + AR6 + AR7 + AR8 + AR9
    
    AR_index = AR_index.rename("AR_index")
    ds3 = xr.merge([ds3, AR_index])

    return ds3

def create_dataframe_max_values(ds3):
    ## create table with max value within extent
    ext=[-141., -130., 54., 60.]
    tmp = ds3.sel(lat=slice(ext[2], ext[3]), lon=slice(ext[0], ext[1]))
    ## find max value in domain
    maxval = tmp.max(dim=['lat', 'lon']).fillna(0) 
    df = maxval.to_dataframe()
    df = df.drop(['init_date'], axis=1)
    ## find 90th percentile value in domain
    # maxval = tmp.quantile(0.9, dim=['lat', 'lon']).fillna(0) 
    # df = maxval.to_dataframe()
    # df = df.drop(['quantile'], axis=1)
    
    df['ivt'] = df['ivt']*100
    df['freezing_level'] = df['freezing_level']*100
    df['uv'] = df['uv']*100
    df['qpf'] = df['qpf']*100
    df = df.rename(columns={"ivt": "IVT", "freezing_level": "Freezing Level", "uv": "UV", "duration": "Duration", "qpf": "QPF"})
    
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

def plot_heatmap(fig, gs, df, init_time, date_lbl, fdate):

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
                "QPF": {
                    "cmap_name" : "mclimate_blue",
                    "ytcklbl" : False,
                    "xtcklbl" : 'QPF'
                  },
                }
    ext=[-141., -130., 54., 60.]
    
    ## loop through each heatmap
    varname_lst = ['IVT', 'Freezing Level', 'UV', 'Duration', 'QPF']
    col_lst = [0, 1, 2, 3, 4]
    for i, (col, varname) in enumerate(zip(col_lst, varname_lst)):
        ax = fig.add_subplot(gs[1:-1, col])
        print(varname)        
        create_mini_heatmap(ax, df, plot_dict[varname]['cmap_name'], varname, 
                            plot_dict[varname]['ytcklbl'], plot_dict[varname]['xtcklbl'])
        if i == 0:
            # ax.set_title(init_time, fontsize=11, loc='left')
    
            lbl_loc = [1, 4.5, 8.5, 12.5, 16.5, 20.5, 24.5, 28.5, 32.5, 36.5]
            for j, datel in enumerate(date_lbl):
                ## add month day labels
                kw = {'weight': 'bold'}
                ax.text(-5., lbl_loc[j]+1.25, textwrap.fill(datel, width=3), va='bottom', ha='center',
                    rotation='horizontal', rotation_mode='anchor', **kw)
    
    
    kw_ticklabels = {'color': 'dimgray', 'weight': 'light'}
    domain = u"{:.0f}\N{DEGREE SIGN}N to {:.0f}\N{DEGREE SIGN}N, {:.0f}\N{DEGREE SIGN}W to {:.0f}\N{DEGREE SIGN}W".format(ext[2], ext[3], ext[0], ext[1])
    txt = 'Maximum percentile rank (xth) in {0}'.format(domain)
    ann_ax = fig.add_subplot(gs[-1, :5])
    ann_ax.axis('off')
    ann_ax.annotate(textwrap.fill(txt, 35), # this is the text
                (0, 0.), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(-80,5), # distance from text to points (x,y)
                ha='left', # horizontal alignment can be left, right or center
                **kw_ticklabels)

    return fig

def create_csv_max_values_only(ds, fdate):
    # create dataframe with max values
    print(' ...... creating dataframe with maximum values ...')
    df, init_time, date_lbl = create_dataframe_max_values(ds)

    ## save as csv
    out_path = path_to_data+'mclimate_csv/'
    # Ensure directory exists
    output_dir = os.path.dirname(out_path)
    os.makedirs(out_path, exist_ok=True)
    
    csv_fname = out_path + 'mclimate_init{0}.csv'.format(fdate)
    df.to_csv(csv_fname, index=True)

    return None

def plot_mclimate_forecast_four_panel(ds, fc, step, fname, domain, impact_date, fdate):
    if domain == 'SEAK':
        ext = [-141., -130., 54., 60.]

    else:
        ext = [-170., -120., 40., 65.]
        
    ls = ds.isel(lat=0).lat.values
    le = ds.isel(lat=-1).lat.values

    if ls < le:
        ds = ds.sel(lon=slice(ext[0], ext[1]), lat=slice(ext[2], ext[3]))
        fc = fc.sel(lon=slice(ext[0], ext[1]), lat=slice(ext[2], ext[3]))
    else:
        ds = ds.sel(lon=slice(ext[0], ext[1]), lat=slice(ext[3], ext[2]))
        fc = fc.sel(lon=slice(ext[0], ext[1]), lat=slice(ext[3], ext[2]))

    ts = pd.to_datetime(ds.init_date.values, format="%Y%m%d%H") 
    init_date = ts.strftime('%Y%m%d%H')
    init_time = ts.strftime('%HZ %d %b %Y')
    start_date = ts - timedelta(days=45)
    start_date = start_date.strftime('%d-%b')
    end_date = ts + timedelta(days=45)
    end_date = end_date.strftime('%d-%b')
    ts_valid = ts + timedelta(hours=int(step))
    valid_time = ts_valid.strftime('%HZ %d %b %Y')
    left_lbl = 'Initialized: {0}'.format(init_time)
    right_lbl = 'F-{0} | Valid: {1}'.format(int(step), valid_time)
    
    # Set up projection
    mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()
    
    # Set tick/grid locations
    lats = ds.lat.values
    lons = ds.lon.values
    if domain == 'NPAC':
        dx = [-160, -150, -140, -130]
        dy = [45., 50., 55., 60.]
    elif domain == 'SEAK':
        dx = [-140, -135, -130]
        dy = [54., 56., 58., 60.]
    else:
        dx = np.arange(lons.min().round(),lons.max().round()+10,10)
        dy = np.arange(lats.min().round(),lats.max().round()+10,10)
    
    # Create figure
    fig = plt.figure(figsize=(11.75, 14.))
    fig.dpi = 300
    fmt = 'png'

    current_dpi=300
    base_dpi=100
    scaling_factor = (current_dpi / base_dpi)**0.3

    set_cw3e_font(current_dpi, scaling_factor)
    
    nrows = 9
    ncols = 8
    
    # contour labels
    kw_clabels = {'inline': True, 'inline_spacing': 7, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    
    kw_ticklabels = {'color': 'dimgray', 'weight': 'light'}
    
    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, height_ratios=[0.05, 0.45, 0.05, 0.05, 0.5, 0.05, 0.05, 1, 0.05],
              width_ratios = [0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 1, 1], wspace=0.05, hspace=0.15)

    ## use gs[rows index, columns index] to access grids

    ## add heatmap
    # create dataframe with max values
    print(' ...... creating dataframe with maximum values ...')
    df, init_time, date_lbl = create_dataframe_max_values(ds)

    ## save as csv
    out_path = path_to_data+'mclimate_csv/'
    # Ensure directory exists
    output_dir = os.path.dirname(out_path)
    os.makedirs(out_path, exist_ok=True)
    
    csv_fname = out_path + 'mclimate_init{0}.csv'.format(fdate)
    df.to_csv(csv_fname, index=True)
    print(' ...... Plotting Heatmaps ...')
    fig = plot_heatmap(fig, gs, df, init_time, date_lbl, fdate)
    print(' ...... Plotting Mclimate maps ...')
    ## mclimate maps
    row_lst = [0, 0, 4, 4]
    row_lst2 = [2, 2, 5, 5]
    col_lst = [6, 7, 6, 7]
    var_lst = ['ivt', 'freezing_level', 'uv', 'qpf']
    llat_lst = [True, False, True, False]
    for i, (row, col) in enumerate(zip(row_lst, col_lst)):
        var = var_lst[i]
        ## percentile
        ax = fig.add_subplot(gs[row:row_lst2[i], col], projection=mapcrs)
        ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=llat_lst[i], right_lats=False, bottom_lons=True)
        
        ## set cmap and contour values based on varname
        if var == 'ivt':
            cmap_name = 'mclimate_green'
            clevs = np.arange(250., 2100., 250.)
        elif var == 'freezing_level':
            cmap_name = 'mclimate_red'
            clevs = np.arange(0., 60000., 2000.)
            fc[var] = fc[var]*3.281 # convert to feet
        elif var == 'uv':
            cmap_name = 'mclimate_purple'
            clevs = np.arange(0., 55., 5.)
        elif var == 'qpf':
            cmap_name = 'mclimate_blue'
            clevs = [0.1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
        
        # Contour Filled (mclimate values)
        data = ds.sel(step=step)[var].values*100.
        cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
        cf = ax.pcolormesh(lons, lats, data, transform=datacrs,
                           cmap=cmap, norm=norm, alpha=0.9)

        # Contour Lines (forecast values)
        forecast = fc[var].sel(step=step)     
        cs = ax.contour(lons, lats, forecast, transform=datacrs,
                         levels=clevs, colors='k',
                         linewidths=0.75, linestyles='solid')
        plt.clabel(cs, **kw_clabels)

        ## Plot Normalized Vectors
        kw_quiver = {'headlength': 6, 'headaxislength': 4.5, 'headwidth': 4.5}
        if var == 'ivt':
            forecast = fc.sel(step=step) 
            fc_mask = forecast.where((forecast.ivt > 250.))
            
            fcu = fc_mask['ivtu'] / fc_mask['ivt']
            fcv = fc_mask['ivtv'] / fc_mask['ivt']

            q = ax.quiver(lons, lats, fcu, fcv, color='k', regrid_shape=20,
                          capstyle='round', units='width', **kw_quiver)

        if var == 'uv':
            forecast = fc.sel(step=step) 
            fc_mask = forecast.where((forecast.uv > 20.))
            
            fcu = fc_mask['u'] / fc_mask['uv']
            fcv = fc_mask['v'] / fc_mask['uv']

            q = ax.quiver(lons, lats, fcu, fcv, color='0.7', regrid_shape=20,
                          capstyle='round', units='width', **kw_quiver)
        
        # Add color bar
        cbax = plt.subplot(gs[row_lst2[i],col]) # colorbar axis
        cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
        cb = Colorbar(ax = cbax, mappable = cf, orientation = 'horizontal', 
                      ticklocation = 'bottom', ticks=cbarticks)
        cb.set_label(cbarlbl)

        ## add box if domain is NPAC
        if domain == 'NPAC': 
            bbox_ext = [-141., -130., 54., 60.]
            ax.add_patch(mpatches.Rectangle(xy=[bbox_ext[0], bbox_ext[2]], width=bbox_ext[1]-bbox_ext[0], height=bbox_ext[3]-bbox_ext[2],
                                        fill=False,
                                        edgecolor='k',
                                        linewidth=0.75,
                                        transform=datacrs,
                                        zorder=199))

        if i == 0:
            ax.set_title(left_lbl, loc='left')
        elif i == 1:
            ax.set_title(right_lbl, loc='right')

    #####################
    ### AR INDEX PLOT ###
    #####################
    ax = fig.add_subplot(gs[7, 6:], projection=mapcrs)
    ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=True, right_lats=False, bottom_lons=True)
    # Contour Filled (mclimate values)
    data = ds.sel(step=step)['AR_index'].values
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap('ar_index')
    cf = ax.pcolormesh(lons, lats, data, transform=datacrs,
                       cmap=cmap, norm=norm, alpha=0.9)

    ## add box if domain is NPAC
    if domain == 'NPAC': 
        bbox_ext = [-141., -130., 54., 60.]
        ax.add_patch(mpatches.Rectangle(xy=[bbox_ext[0], bbox_ext[2]], width=bbox_ext[1]-bbox_ext[0], height=bbox_ext[3]-bbox_ext[2],
                                    fill=False,
                                    edgecolor='k',
                                    linewidth=0.75,
                                    transform=datacrs,
                                    zorder=199))

    # Add color bar
    cbax = plt.subplot(gs[8, 6:]) # colorbar axis
    cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'horizontal', 
                  ticklocation = 'bottom', ticks=cbarticks)
    cb.set_label(cbarlbl)
        
    txt = 'Relative to all {2}-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date, step)
    ann_ax = fig.add_subplot(gs[6, 6:])
    ann_ax.axis('off')
    ann_ax.annotate(textwrap.fill(txt, 101), # this is the text
               (0, 0.3), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(0,-24), # distance from text to points (x,y)
                ha='left', # horizontal alignment can be left, right or center
                **kw_ticklabels)

    print(fname)
    fig.savefig('%s.%s' %(fname, fmt), bbox_inches='tight', dpi=fig.dpi)

    plt.close(fig)
    
def output_compare_mclimate_to_reforecast(fdate, model, impact_date=None, plot=True):
    fig_path = path_to_data+'mclimate_images/mclimate_{0}/'.format(fdate)  
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    
    ####################################
    ### COMPARE FORECAST TO MCLIMATE ###
    ####################################
    print(' ...... running Mclimate comparison ...')
    var_lst = ['qpf', 'ivt', 'freezing_level', 'uv1000']
    ds_lst = []
    fc_lst = []
    for i, varname in enumerate(var_lst):
        print('......... for {0} ...'.format(varname))
        forecast, ds = mclim_func.run_compare_mclimate_forecast(varname, fdate, model, server='expanse')
        fc_lst.append(forecast)
        if varname == 'uv1000':
                ds = ds.rename({'mclimate': 'uv'})
        else:
            ds = ds.rename({'mclimate': varname})
        ds_lst.append(ds)
        ds.close()
        forecast.close()
        
    ### merge the datasets
    ds3 = xr.merge(ds_lst)
    ds3 = ds3.sortby('lat')
    
    fc = xr.merge(fc_lst)
    fc = fc.sortby('lat')
    fc = fc.rename({'tp': 'qpf'})

    ## delete ds_lst and fc_lst
    del ds_lst
    del fc_lst

    ## compute IVT and UV direction relative to topography
    ivtdir_diff, uvdir_diff = compute_ivt_uv_direction_relative_to_slope(fc, fdate)

    ## add the dir_diff vars to the final dataset
    ds3 = ds3.assign({"ivtdir_diff": ivtdir_diff,
                    "uvdir_diff": uvdir_diff
                   })
    
    ## compute AR duration and AR Hazard Index value
    print(ds3)
    ds3 = compute_AR_duration_AR_impact_index(ds3)

    if plot == False:
        create_csv_max_values_only(ds3, fdate)
    elif plot == True:
        ####################
        ### CREATE PLOTS ###
        ####################
        print(' ...... creating four panel plot ...')
        step_lst = np.arange(6, 168+6, 6)
        ds3 = ds3.sel(step=step_lst)
        print("Running gc.collect()")
        gc.collect()
        # step_lst = ds3.step.values
        for i, step in enumerate(step_lst):
            print(step)
            out_fname = fig_path + 'SEAK_mclimate_F{0}'.format(step)
            plot_mclimate_forecast_four_panel(ds3, fc, step, out_fname, domain="SEAK", impact_date=impact_date, fdate=fdate)
            out_fname = fig_path + 'NPAC_mclimate_F{0}'.format(step)
            plot_mclimate_forecast_four_panel(ds3, fc, step, out_fname, domain="NPAC", impact_date=impact_date, fdate=fdate)

            print("Running gc.collect()")
            gc.collect()

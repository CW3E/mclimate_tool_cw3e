"""
Filename:    plotter.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for plotting
"""

# Import Python modules

import os, sys
import numpy as np
import itertools
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import pandas as pd
import cmocean.cm as cmo
from matplotlib.colorbar import Colorbar # different way to handle colorbar
from matplotlib.gridspec import GridSpec
from datetime import timedelta
import textwrap

import matplotlib as mpl
mpl.use('agg')

## import personal modules
import custom_cmaps as ccmap
    
def draw_basemap(ax, datacrs=ccrs.PlateCarree(), extent=None, xticks=None, yticks=None, grid=False, left_lats=True, right_lats=False, bottom_lons=True, mask_ocean=False, coastline=True):
    """
    Creates and returns a background map on which to plot data. 
    
    Map features include continents and country borders.
    Option to set lat/lon tickmarks and draw gridlines.
    
    Parameters
    ----------
    ax : 
        plot Axes on which to draw the basemap
    
    datacrs : 
        crs that the data comes in (usually ccrs.PlateCarree())
        
    extent : float
        Set map extent to [lonmin, lonmax, latmin, latmax] 
        Default: None (uses global extent)
        
    grid : bool
        Whether to draw grid lines. Default: False
        
    xticks : float
        array of xtick locations (longitude tick marks)
    
    yticks : float
        array of ytick locations (latitude tick marks)
        
    left_lats : bool
        Whether to add latitude labels on the left side. Default: True
        
    right_lats : bool
        Whether to add latitude labels on the right side. Default: False
        
    Returns
    -------
    ax :
        plot Axes with Basemap
    
    Notes
    -----
    - Grayscale colors can be set using 0 (black) to 1 (white)
    - Alpha sets transparency (0 is transparent, 1 is solid)
    
    """
    ## some style dictionaries
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    kw_grid = {'linewidth': .5, 'color': 'k', 'linestyle': '--', 'alpha': 0.4}
    kw_ticks = {'length': 4, 'width': 0.5, 'pad': 2, 'color': 'black',
                         'labelsize': 10, 'labelcolor': 'dimgray'}

    # Use map projection (CRS) of the given Axes
    mapcrs = ax.projection    
    
    # Add map features (continents and country borders)
    ax.add_feature(cfeature.LAND, facecolor='0.9')      
    ax.add_feature(cfeature.BORDERS, edgecolor='0.4', linewidth=0.8)
    if coastline == True:
        ax.add_feature(cfeature.COASTLINE, edgecolor='0.4', linewidth=0.8)
    if mask_ocean == True:
        ax.add_feature(cfeature.OCEAN, edgecolor='0.4', zorder=12, facecolor='white') # mask ocean
        
    ## Tickmarks/Labels
    ## Add in meridian and parallels
    if mapcrs == ccrs.NorthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
    elif mapcrs == ccrs.SouthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
        
    else:
        gl = ax.gridlines(crs=datacrs, draw_labels=True, **kw_grid)
        gl.top_labels = False
        gl.left_labels = left_lats
        gl.right_labels = right_lats
        gl.bottom_labels = bottom_lons
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = kw_ticklabels
        gl.ylabel_style = kw_ticklabels
    
    ## Gridlines
    # Draw gridlines if requested
    if (grid == True):
        gl.xlines = True
        gl.ylines = True
    if (grid == False):
        gl.xlines = False
        gl.ylines = False
            

    # apply tick parameters
    ax.set_xticks(xticks, crs=datacrs)
    ax.set_yticks(yticks, crs=datacrs)
    plt.yticks(color='w', size=1) # hack: make the ytick labels white so the ticks show up but not the labels
    plt.xticks(color='w', size=1) # hack: make the ytick labels white so the ticks show up but not the labels
    ax.ticklabel_format(axis='both', style='plain')

    ## Map Extent
    # If no extent is given, use global extent
    if extent is None:        
        ax.set_global()
        extent = [-180., 180., -90., 90.]
    # If extent is given, set map extent to lat/lon bounding box
    else:
        ax.set_extent(extent, crs=datacrs)
    
    return ax

def plot_mclimate_forecast(ds, fc, step, varname, fname, ext=[-170., -120., 50., 75.]):
    ds = ds.sel(lon=slice(ext[0], ext[1]), lat=slice(ext[3], ext[2]))
    fc = fc.sel(lon=slice(ext[0], ext[1]), lat=slice(ext[3], ext[2]))
    if varname == 'uv1000':
        varname = 'uv'
    ts = pd.to_datetime(ds.init_date.values, format="%Y%m%d%H") 
    init_date = ts.strftime('%Y%m%d%H')
    # Set up projection
    mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()
    
    # Set tick/grid locations
    lats = ds.lat.values
    lons = ds.lon.values
    if ext == [-170., -120., 40., 65.]:
        dx = [-160, -150, -140, -130]
        dy = [45., 50., 55., 60.]
    elif ext == [-141., -130., 54., 60.]:
        dx = [-140, -135, -130]
        dy = [54., 56., 58., 60.]
    else:
        dx = np.arange(lons.min().round(),lons.max().round()+10,10)
        dy = np.arange(lats.min().round(),lats.max().round()+10,10)
    
    # Create figure
    fig = plt.figure(figsize=(9.5, 6.25))
    fig.dpi = 600
    fmt = 'png'
    
    nrows = 3
    ncols = 1
    
    # contour labels
    kw_clabels = {'fontsize': 7, 'inline': True, 'inline_spacing': 7, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    
    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, height_ratios=[1, 0.05, 0.05], width_ratios = [1], wspace=0.05, hspace=0.1)
    ## use gs[rows index, columns index] to access grids
    
    ax = fig.add_subplot(gs[0, 0], projection=mapcrs)
        
    ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=True, right_lats=False, bottom_lons=True)
    
    ## set cmap and contour values based on varname
    if varname == 'ivt':
        cmap_name = 'mclimate_red'
        clevs = np.arange(250., 2100., 250.)
    elif varname == 'freezing_level':
        cmap_name = 'mclimate_green'
        clevs = np.arange(0., 60000., 2000.)
        fc[varname] = fc[varname]*3.281 # convert to feet
    elif varname == 'uv':
        cmap_name = 'mclimate_purple'
        clevs = np.arange(0., 55., 5.)
    
    # Contour Filled (mclimate values)
    data = ds.sel(step=step).mclimate.values*100.
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
    cf = ax.pcolormesh(lons, lats, data, transform=datacrs,
                       cmap=cmap, norm=norm, alpha=0.9)
    # cf = ax.contourf(lons, lats, data, transform=datacrs,
    #                  levels=bnds, cmap=cmap, norm=norm, alpha=0.9, extend='neither')
    
    # Contour Lines (forecast values)
    forecast = fc.sel(step=step)     
    cs = ax.contour(lons, lats, forecast[varname], transform=datacrs,
                     levels=clevs, colors='k',
                     linewidths=0.75, linestyles='solid')
    plt.clabel(cs, **kw_clabels)
    
    # Add color bar
    cbax = plt.subplot(gs[1,0]) # colorbar axis
    cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'horizontal', 
                  ticklocation = 'bottom', ticks=cbarticks)
    cb.set_label(cbarlbl, fontsize=11)
    cb.ax.tick_params(labelsize=12)
    
    init_time = ts.strftime('%HZ %d %b %Y')
    start_date = ts - timedelta(days=45)
    start_date = start_date.strftime('%d-%b')
    end_date = ts + timedelta(days=45)
    end_date = end_date.strftime('%d-%b')
    
    ts_valid = ts + timedelta(hours=int(step))
    valid_time = ts_valid.strftime('%HZ %d %b %Y')
    
    ax.set_title('Initialized: {0}'.format(init_time), loc='left', fontsize=10)
    ax.set_title('F-{0} | Valid: {1}'.format(int(step), valid_time), loc='right', fontsize=10)

    
    txt = 'Relative to all {2}-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date, step)
    ann_ax = fig.add_subplot(gs[-1, 0])
    ann_ax.axis('off')
    ann_ax.annotate(textwrap.fill(txt, 101), # this is the text
               (0, 0.3), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(0,-19), # distance from text to points (x,y)
                ha='left', # horizontal alignment can be left, right or center
                **kw_ticklabels)
    
    fig.savefig('%s.%s' %(fname, fmt), bbox_inches='tight', dpi=fig.dpi)

    plt.close(fig)

def plot_mclimate_forecast_comparison(ds_lst, fc_lst, varname, fname, ext=[-170., -120., 40., 65.]):
    if varname == 'uv1000':
        varname = 'uv'
    # Set up projection
    mapcrs = ccrs.Mercator()
    # mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()
    
    # Set tick/grid locations
    lats = fc_lst[0].lat.values
    lons = fc_lst[0].lon.values
    dx = np.arange(lons.min().round(),lons.max().round()+10,10)
    dy = np.arange(lats.min().round(),lats.max().round()+5,5)
    
    # Create figure
    fig = plt.figure(figsize=(13, 5))
    fig.dpi = 300
    fmt = 'png'
    
    nrows = 1
    ncols = 3
    
    # contour labels
    kw_clabels = {'fontsize': 7, 'inline': True, 'inline_spacing': 7, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    
    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, height_ratios=[1], width_ratios = [1, 1, 0.05], wspace=0.001, hspace=0.05)
    ## use gs[rows index, columns index] to access grids
    
    ###################
    ### PLOT FIGURE ###
    ###################
    leftlats_lst = [True, False]
    for i, (fc, ds) in enumerate(zip(fc_lst, ds_lst)):
        ax = fig.add_subplot(gs[0, i], projection=mapcrs) 
        ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=leftlats_lst[i], right_lats=False, bottom_lons=True)
        
        ## set cmap and contour values based on varname
        if varname == 'ivt':
            cmap_name = 'mclimate_red'
            clevs = np.arange(250., 2100., 250.)
        elif varname == 'freezing_level':
            cmap_name = 'mclimate_green'
            clevs = np.arange(0., 60000., 2000.)
            fc[varname] = fc[varname]*3.281 # convert to feet
        elif varname == 'uv':
            cmap_name = 'mclimate_purple'
            clevs = np.arange(0., 55., 5.)
        
        # Contour Filled
        data = ds.mclimate.values*100.    
        cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
        # cf = ax.contourf(ds.lon, ds.lat, data, transform=datacrs,
        #                  levels=bnds, cmap=cmap, norm=norm, alpha=0.9, extend='neither')
        cf = ax.pcolormesh(lons, lats, data, transform=datacrs,
                       cmap=cmap, norm=norm, alpha=0.9)
        
        # Contour Lines
        cs = ax.contour(fc.lon, fc.lat, fc[varname], transform=datacrs,
                         levels=clevs, colors='k',
                         linewidths=0.75, linestyles='solid')
        plt.clabel(cs, **kw_clabels)
        
        ts = pd.to_datetime(str(fc.init_date.values)) 
        init_time = ts.strftime('%HZ %d %b %Y')
        start_date = ts - timedelta(days=45)
        start_date = start_date.strftime('%d-%b')
        end_date = ts + timedelta(days=45)
        end_date = end_date.strftime('%d-%b')
        
        ts = pd.to_datetime(str(fc.valid_time.values)) 
        valid_time = ts.strftime('%HZ %d %b %Y')
        
        ax.set_title('Model Run: {0}'.format(init_time), loc='left', fontsize=10)
        ax.set_title('Valid Date: {0}'.format(valid_time), loc='right', fontsize=10)
    
        
        txt = 'Relative to all {2}-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date, fc.step.values)
        ann_ax = fig.add_subplot(gs[-1, i])
        ann_ax.axis('off')
        ann_ax.annotate(textwrap.fill(txt, 60), # this is the text
                   (0, 0.), # these are the coordinates to position the label
                    textcoords="offset points", # how to position the text
                    xytext=(25,-35), # distance from text to points (x,y)
                    ha='left', # horizontal alignment can be left, right or center
                    **kw_ticklabels)
    
    # Add color bar
    cbax = plt.subplot(gs[0,-1]) # colorbar axis
    cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'vertical', 
                  ticklocation = 'right', ticks=cbarticks)
    cb.set_label(cbarlbl, fontsize=10)
    cb.ax.tick_params(labelsize=8)
    
    fig.savefig('%s.%s' %(fname, fmt), bbox_inches='tight', dpi=fig.dpi)
    
    # Show
    plt.show()
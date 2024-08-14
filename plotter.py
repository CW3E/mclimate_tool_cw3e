"""
Filename:    plotter.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for plotting
"""

# Import Python modules

import os, sys
import numpy as np
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

def plot_mclimate_forecast(ds, fc, step, varname):
    ts = pd.to_datetime(ds.init_date.values, format="%Y%m%d%H") 
    init_date = ts.strftime('%Y%m%d%H')
    # Set up projection
    mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()
    
    # Set tick/grid locations
    lats = ds.lat.values
    lons = ds.lon.values
    dx = np.arange(lons.min().round(),lons.max().round()+10,10)
    dy = np.arange(lats.min().round(),lats.max().round()+10,10)
    
    ext = [-170., -120., 40., 65.]
    
    # Create figure
    fig = plt.figure(figsize=(9.5, 6.25))
    fig.dpi = 300
    # fname = 'figs/{2}_mclimate_{0}_F{1}'.format(init_date, step, varname)
    fname = 'figs/{0}_mclimate_F{1}'.format(varname, int(step))
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
    
    # Contour Filled (mclimate values)
    data = ds.sel(step=step).mclimate.values*100.
    if varname == 'ivt':
        cmap, norm, bnds = ccmap.cmap('mclimate')
    elif varname == 'freezing_level':
        cmap, norm, bnds = ccmap.cmap('mclimate_purple')
    cf = ax.contourf(lons, lats, data, transform=datacrs,
                     levels=bnds, cmap=cmap, norm=norm, alpha=0.9, extend='neither')
    
    # Contour Lines (forecast values)
    forecast = fc.sel(step=step)
    if varname == 'ivt':
        clevs = np.arange(250., 2100., 250.)
    elif varname == 'freezing_level':
        clevs = np.arange(0., 18000., 1500.)
        forecast[varname] = forecast[varname]*3.281 # convert to feet
        
    cs = ax.contour(lons, lats, forecast[varname], transform=datacrs,
                     levels=clevs, colors='k',
                     linewidths=0.75, linestyles='solid')
    plt.clabel(cs, **kw_clabels)
    
    # Add color bar
    cbax = plt.subplot(gs[1,0]) # colorbar axis
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'horizontal', ticklocation = 'bottom')
    cb.set_label('Model Climate Percentile Rank (xth)', fontsize=11)
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

    
    txt = 'Relative to all 162-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date)
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
"""
Filename:    datahub.py
Author:      Ricardo Vilela, rbatistavilela@ucsd.edu and Deanna Nash, dnash@ucsd.edu
Description: Functions to create plain png of mclimate comparison and .json files for leaflet.
"""

from datetime import datetime, timedelta
import numpy as np
import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import cm, colors
import json              
import xarray as xr
import os
from pyproj import Transformer
import pandas as pd
import pyproj
import pytz
import custom_cmaps as ccmap

def create_folder(filename):
    '''
    :param path: path string
    :return:
    '''

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
        
    return None

def create_textstrings(ds):
    ts = pd.to_datetime(ds.init_date.values, format="%Y%m%d%H")
    init_time = ts.strftime('%HZ %d %b %Y')
    start_date = ts - timedelta(days=45)
    start_date = start_date.strftime('%d-%b')
    end_date = ts + timedelta(days=45)
    end_date = end_date.strftime('%d-%b')
    
    txtstring1 = []
    txtstring2 = []
    for i, step in enumerate(ds.step.values):
        ts_valid = ts + timedelta(hours=int(step))
        valid_time = ts_valid.strftime('%HZ %d %b %Y')

        ## text strings
        txt1 = 'Initialized: {0} | F-{1} | Valid: {2}'.format(init_time, int(step), valid_time)

        txt2 = 'Relative to all {2}-h GEFSv12 reforecasts initialized between {0} and {1} (2000-2019)'.format(start_date, end_date, step)
        txtstring1.append(txt1)
        txtstring2.append(txt2)
    
    return txtstring1, txtstring2
  
def mclimate_figure_web(ds, varname, step, filename):
    print('[INFO] Generating figure')
    
    data = ds.sel(step=step)[varname].values*100.
    lon, lat = np.meshgrid(ds.lon.values,ds.lat.values)

    ## set cmap and contour values based on varname
    if varname == 'ivt':
        cmap_name = 'mclimate_green'
    elif varname == 'freezing_level':
        cmap_name = 'mclimate_red'
    elif varname == 'uv':
        cmap_name = 'mclimate_purple'
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)

    ## update projection of the data and lat/lons
    wgs84 = pyproj.CRS("EPSG:4326")
    web_mercator = pyproj.CRS("EPSG:3857")
    projector = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)
    x, y = projector.transform(lon, lat)

    my_dpi = 500
    fig = plt.figure(frameon=False, dpi=my_dpi)

    plt.xticks([])
    plt.yticks([])
    plt.axis('off')
    
    ## Filled Contour
    plt.pcolormesh(x, y, data, cmap=cmap, norm=norm)

    plt.gca().set_aspect('equal')
    create_folder(filename)
    plt.savefig(filename,bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close()
    
def forecast_figure_web(fc, varname, step, filename):
    print('[INFO] Generating figure')

    lon, lat = np.meshgrid(fc.lon.values, fc.lat.values)

    ## set cmap and contour values based on varname
    if varname == 'ivt':
        clevs = np.arange(250., 2100., 250.)
    elif varname == 'freezing_level':
        clevs = np.arange(0., 60000., 2000.)
        fc[varname] = fc[varname]*3.281 # convert to feet
    elif varname == 'uv':
        clevs = np.arange(0., 55., 5.)

    ## update projection of the data and lat/lons
    wgs84 = pyproj.CRS("EPSG:4326")
    web_mercator = pyproj.CRS("EPSG:3857")
    projector = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)
    x, y = projector.transform(lon, lat)

    my_dpi = 500
    fig = plt.figure(frameon=False, dpi=my_dpi)

    plt.xticks([])
    plt.yticks([])
    plt.axis('off')

    # Contour Lines (forecast values)
    forecast = fc[varname].sel(step=step)
    cs = plt.contour(x, y, forecast, levels=clevs, colors='k',
                     linewidths=0.75, linestyles='solid')
    
    # contour labels
    kw_clabels = {'fontsize': 7, 'inline': True, 'inline_spacing': 7, 'fmt': '%i',
                  'rightside_up': True, 'use_clabeltext': True}
    plt.clabel(cs, **kw_clabels)

    plt.gca().set_aspect('equal')
    create_folder(filename)
    plt.savefig(filename,bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close()
    
def build_json(filelist, timelist, timelist2, jsoninfo):
    print('[INFO] Generating webserver Json file')
    destination_relative_filenames = []
    destination_filenames = []
        
    for index, filename in enumerate(filelist):
       
        destination_relative_filenames.append("map_files/"+filename)
        
    d = {"name":jsoninfo["sourcename"], "images":destination_relative_filenames,"timestamps":timelist,"textstring":timelist2,"bounds":jsoninfo["bounds"]}
    json_object = json.dumps(d, indent=4)
    with open(jsoninfo["filename"], "w") as outfile:
        outfile.write(json_object)

    line_prepender(jsoninfo["filename"],jsoninfo["dictionary_variable"]+" =")
    print('[INFO] file saved: ',jsoninfo["filename"])

def line_prepender(filename, line):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content)
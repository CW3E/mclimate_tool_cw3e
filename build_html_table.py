#!/usr/bin/python3
"""
Filename:    build_html_table.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: functions to build interactive html table for website
"""

import numpy as np
import pandas as pd
import xarray as xr
from datetime import timedelta


def highlight_1(s, props=''):
    # return np.where(s == 100, props, '')
    return np.where(s.str.contains('^100'), props, '')

def highlight_99(s, props=''):
    # return np.where(s == 99, props, '')
    return np.where(s.str.contains('^99'), props, '')

def highlight_98(s, props=''):
    # return np.where(s == 98, props, '')
    return np.where(s.str.contains('^98'), props, '')

def highlight_97(s, props=''):
    # return np.where(s == 97, props, '')
    return np.where(s.str.contains('^97'), props, '')

def highlight_96(s, props=''):
    # return np.where(s == 96, props, '')
    return np.where(s.str.contains('^96'), props, '')

def highlight_95(s, props=''):
    # return np.where(s == 95, props, '')
    return np.where(s.str.contains('^95'), props, '')

def highlight_90_94(s, props=''):
    # return np.where((s >= 90) & (s <= 94), props, '')
    idx = (s.str.contains('^94')) | (s.str.contains('^93')) | (s.str.contains('^92')) | (s.str.contains('^91')) | (s.str.contains('^90')) 
    return np.where(idx, props, '')

def highlight_75(s, props=''):
    # return np.where(s == 75, props, '')
    return np.where(s.str.contains('^75'), props, '')

def highlight_0(s, props=''):
    # return np.where(s == 0, props, '')
    return np.where(s.str.contains('^0'), props, '')
   
def make_clickable_Z0(s):
    z0_val, step = s.split(";")
    z0_val = int(z0_val)
    fname = 'images/images_operational/freezing_level_mclimate_F{0}.png'.format(step)
    string_arg = "image.src='{0}'".format(fname)
    if z0_val >= 98:
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:white>{1}</a>'.format(string_arg, z0_val)
    else: 
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:black>{1}</a>'.format(string_arg, z0_val)
    return link

def make_clickable_ivt(s):
    ivt_val, step = s.split(";")
    ivt_val = int(ivt_val)
    fname = 'images/images_operational/ivt_mclimate_F{0}.png'.format(step)
    string_arg = "image.src='{0}'".format(fname)
    if ivt_val >= 98:
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:white>{1}</a>'.format(string_arg, ivt_val)
    else: 
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:black>{1}</a>'.format(string_arg, ivt_val)
    return link

def make_clickable_uv1000(s):
    uv1000_val, step = s.split(";")
    uv1000_val = int(uv1000_val)
    fname = 'images/images_operational/uv1000_mclimate_F{0}.png'.format(step)
    string_arg = "image.src='{0}'".format(fname)
    if uv1000_val >= 98:
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:white>{1}</a>'.format(string_arg, uv1000_val)
    else: 
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:black>{1}</a>'.format(string_arg, uv1000_val)
    return link

def make_clickable_F(s):
    domain, step = s.split(";")
    fname = 'images/images_operational/{1}_mclimate_F{0}.png'.format(step, domain)
    string_arg = "image.src='{0}'".format(fname)
    link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:black>{1}</a>'.format(string_arg, step)
    return link
    
def create_html_table(ds, domain):
    if domain == 'SEAK':
        ext = [-141., -130., 54., 60.]
    else:
        ext = [-170., -120., 40., 65.]
        
    ## create html table with max value within extent
    tmp = ds.sel(lat=slice(ext[2], ext[3]), lon=slice(ext[0], ext[1]))
    maxval = tmp.max(dim=['lat', 'lon']).fillna(0)
    
    ## create list of valid dates
    ts = pd.to_datetime(ds.init_date.values, format="%Y%m%d%H")
    # ts = ds.init_date.values
    init_date = ts.strftime('%Y%m%d%H')
    init_time = ts.strftime('Initialized: %HZ %d %b %Y')
    col2 = []
    col3 = []
    step_lst = ds.step.values.tolist()
    for i, step in enumerate(step_lst):
        ts_valid = ts + timedelta(hours=step)
        col2.append(ts_valid.strftime('%a %d'))
        col3.append(ts_valid.strftime('%HZ'))

    str_lst = []
    for i, step_val in enumerate(step_lst):
        row_str = '{0};{1}'.format(domain, step_val)
        str_lst.append(row_str)
        
    ## create multindex dataframe
    arrays = [col2, col3]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=["Date", "Hour"])
    ivt_vals = maxval.ivt.values*100
    fl_vals = maxval.freezing_level.values*100
    uv_vals = maxval.uv.values*100
        
    data = {'F': str_lst,
            'IVT': [f"{num:.0f}" for num in ivt_vals],
            'Z0': [f"{num:.0f}" for num in fl_vals],
            'UV': [f"{num:.0f}" for num in uv_vals]}
    df = pd.DataFrame(data, index=index)
    
    ## get class values based on IVT values
    # class_names = set_classes(maxivt.values, 'IVT')
    
    cell_hover = {'selector': 'td:hover', 'props': [('background-color', '#F5F0E6')]} ## change the color of the cell when hover
    # alt_index = {'selector': 'th:nth-child(even)', 'props': 'background-color: #F5F0E6'} ## change the color of alternating index row
    # lines = {'selector': 'th', 'props': 'border-bottom: 1px solid black; border-left: 1px solid black; border-right: 1px solid black; border-top: 1px solid black;'} ## add a line to the bottom of each row
    index_names = {'selector': '.index_name', 'props': 'font-style: italic; color: darkgrey; font-weight:normal;'}
    # lines2 = {'selector': 'td', 'props': 'border-bottom: 1px solid black; border-left: 1px solid black; border-right: 1px solid black;'} ## add a line to the bottom of each row
    border = {'selector': ' : ', 'props': 'border: 1px solid black'}
    # apply style formatting
    slice_ = ['IVT']
    slice2_ = ['Z0']
    slice3_ = ['UV']
    sliceF_ = ['F']

    df = df.style.format(make_clickable_F, escape="html", na_rep="NA", subset=sliceF_)\
           .apply(highlight_1, props='color:white;background-color: #800026;', axis=0, subset=slice2_)\
           .apply(highlight_99, props='color:white;background-color: #bd0026;', axis=0, subset=slice2_)\
           .apply(highlight_98, props='color:white;background-color: #e31a1c;', axis=0, subset=slice2_)\
           .apply(highlight_97, props='color:black;background-color: #fc4e2a', axis=0, subset=slice2_)\
           .apply(highlight_96, props='color:black;background-color: #fd8d3c', axis=0, subset=slice2_)\
           .apply(highlight_95, props='color:black;background-color: #feb24c', axis=0, subset=slice2_)\
           .apply(highlight_90_94, props='color:black;background-color: #fed976', axis=0, subset=slice2_)\
           .apply(highlight_75, props='color:black;background-color: #ffeda0', axis=0, subset=slice2_)\
           .apply(highlight_0, props='color:black;background-color: #ffffcc', axis=0, subset=slice2_)\
           .apply(highlight_1, props='color:white;background-color: #004529;', axis=0, subset=slice_)\
           .apply(highlight_99, props='color:white;background-color: #238443;', axis=0, subset=slice_)\
           .apply(highlight_98, props='color:white;background-color: #006837;', axis=0, subset=slice_)\
           .apply(highlight_97, props='color:black;background-color: #41ab5d', axis=0, subset=slice_)\
           .apply(highlight_96, props='color:black;background-color: #78c679', axis=0, subset=slice_)\
           .apply(highlight_95, props='color:black;background-color: #addd8e', axis=0, subset=slice_)\
           .apply(highlight_90_94, props='color:black;background-color: #d9f0a3', axis=0, subset=slice_)\
           .apply(highlight_75, props='color:black;background-color: #f7fcb9', axis=0, subset=slice_)\
           .apply(highlight_0, props='color:black;background-color: #ffffe5', axis=0, subset=slice_)\
           .apply(highlight_1, props='color:white;background-color: #4d004b;', axis=0, subset=slice3_)\
           .apply(highlight_99, props='color:white;background-color: #810f7c;', axis=0, subset=slice3_)\
           .apply(highlight_98, props='color:white;background-color: #88419d;', axis=0, subset=slice3_)\
           .apply(highlight_97, props='color:black;background-color: #8c6bb1;', axis=0, subset=slice3_)\
           .apply(highlight_96, props='color:black;background-color: #8c96c6;', axis=0, subset=slice3_)\
           .apply(highlight_95, props='color:black;background-color: #9ebcda;', axis=0, subset=slice3_)\
           .apply(highlight_90_94, props='color:black;background-color: #bfd3e6;', axis=0, subset=slice3_)\
           .apply(highlight_75, props='color:black;background-color: #e0ecf4;', axis=0, subset=slice3_)\
           .apply(highlight_0, props='color:black;background-color: #f7fcfd;', axis=0, subset=slice3_)\
           .set_table_styles([cell_hover, index_names])\
           .set_caption("{0}".format(init_time))


    return df


mclimate_colors = [  # create internal CSS classes
    {'selector': 'td.IVT0.0', 'props': 'background-color: #ffffe5;'},
    {'selector': 'td.IVT0.75', 'props': 'background-color: #f7fcb9;'},
    {'selector': 'td.IVT0.90', 'props': 'background-color: #d9f0a3;'},
    {'selector': 'td.IVT0.91', 'props': 'background-color: #d9f0a3;'},
    {'selector': 'td.IVT0.92', 'props': 'background-color: #d9f0a3;'},
    {'selector': 'td.IVT0.93', 'props': 'background-color: #d9f0a3;'},
    {'selector': 'td.IVT0.94', 'props': 'background-color: #d9f0a3;'},
    {'selector': 'td.IVT0.95', 'props': 'background-color: #addd8e;'},
    {'selector': 'td.IVT0.96', 'props': 'background-color: #78c679;'},
    {'selector': 'td.IVT0.97', 'props': 'background-color: #41ab5d;'},
    {'selector': 'td.IVT0.98', 'props': 'background-color: #006837;'},
    {'selector': 'td.IVT0.99', 'props': 'background-color: #238443;'},
    {'selector': 'td.IVT1.0', 'props': 'background-color: #004529;'}
]

def set_classes(col_vals, varname):
    class_lst = []
    for i, cval in enumerate(col_vals):
        class_val = 'td.{0}{1}'.format(varname, cval)
        class_lst.append(class_val)
    return class_lst
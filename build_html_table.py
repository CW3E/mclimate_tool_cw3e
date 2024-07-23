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


def make_clickable(init_date, step, mclimate_val):
    fname = 'images/mclimate/ivt_mclimate_{0}_F{1}.png'.format(init_date, step)
    string_arg = "image.src='{0}'".format(fname)
    return '<a href="#image" onclick="{0}">{1}</a>'.format(string_arg, mclimate_val)
    # return '<a href="#image" onclick="showImage("images/mclimate/ivt_mclimate_{0}_F{1}.png");">{2}</a>'.format(init_date, step, mclimate_val)

    
def make_clickable_Z0(s):
    z0_val, step = s.split(";")
    z0_val = int(z0_val)
    fname = 'images/freezing_level_mclimate_F{0}.png'.format(step)
    string_arg = "image.src='{0}'".format(fname)
    if z0_val >= 98:
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:white>{1}</a>'.format(string_arg, z0_val)
    else: 
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:black>{1}</a>'.format(string_arg, z0_val)
    return link


def make_clickable_ivt(s):
    ivt_val, step = s.split(";")
    ivt_val = int(ivt_val)
    fname = 'images/ivt_mclimate_F{0}.png'.format(step)
    string_arg = "image.src='{0}'".format(fname)
    if ivt_val >= 98:
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:white>{1}</a>'.format(string_arg, ivt_val)
    else: 
        link = '<a href="#image" onclick="{0}" style=text-decoration:none;color:black>{1}</a>'.format(string_arg, ivt_val)
    return link

def create_html_table(ds, ext):
    
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
    step_lst = ds.step.values
    for i, step in enumerate(step_lst):
        ts_valid = ts + timedelta(hours=int(step))
        col2.append(ts_valid.strftime('%a %d'))
        col3.append(ts_valid.strftime('%HZ'))

    ## create multindex dataframe
    arrays = [col2, col3, ds.step.values]
    tuples = list(zip(*arrays))
    index = pd.MultiIndex.from_tuples(tuples, names=["Date", "Hour", "F"])
    ivt_vals = maxval.IVT.values*100
    fl_vals = maxval.freezing_level.values*100
    
    ivt_str_lst = []
    fl_str_lst = []
    for i, (ivt_val, fl_val, step_val) in enumerate(zip(ivt_vals.astype(int), fl_vals.astype(int), step_lst)):
        ivt_str = '{0};{1}'.format(ivt_val, step_val)
        ivt_str_lst.append(ivt_str)
        fl_str = '{0};{1}'.format(fl_val, step_val)
        fl_str_lst.append(fl_str)
        
    
    # data = {'IVT': ivt_vals.astype(int)}
    data = {'IVT': ivt_str_lst,
            'Z0': fl_str_lst}
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
    df = df.style.format(make_clickable_ivt, escape="html", na_rep="NA", subset=slice_)\
           .format(make_clickable_Z0, escape="html", na_rep="NA", subset=slice2_)\
           .apply(highlight_1, props='color:white;background-color: #004529;', axis=0, subset=slice_)\
           .apply(highlight_99, props='color:white;background-color: #238443;', axis=0, subset=slice_)\
           .apply(highlight_98, props='color:white;background-color: #006837;', axis=0, subset=slice_)\
           .apply(highlight_97, props='color:black;background-color: #41ab5d', axis=0, subset=slice_)\
           .apply(highlight_96, props='color:black;background-color: #78c679', axis=0, subset=slice_)\
           .apply(highlight_95, props='color:black;background-color: #addd8e', axis=0, subset=slice_)\
           .apply(highlight_90_94, props='color:black;background-color: #d9f0a3', axis=0, subset=slice_)\
           .apply(highlight_75, props='color:black;background-color: #f7fcb9', axis=0, subset=slice_)\
           .apply(highlight_0, props='color:black;background-color: #ffffe5', axis=0, subset=slice_)\
           .apply(highlight_1, props='color:white;background-color: #4d004b;', axis=0, subset=slice2_)\
           .apply(highlight_99, props='color:white;background-color: #810f7c;', axis=0, subset=slice2_)\
           .apply(highlight_98, props='color:white;background-color: #88419d;', axis=0, subset=slice2_)\
           .apply(highlight_97, props='color:black;background-color: #8c6bb1;', axis=0, subset=slice2_)\
           .apply(highlight_96, props='color:black;background-color: #8c96c6;', axis=0, subset=slice2_)\
           .apply(highlight_95, props='color:black;background-color: #9ebcda;', axis=0, subset=slice2_)\
           .apply(highlight_90_94, props='color:black;background-color: #bfd3e6;', axis=0, subset=slice2_)\
           .apply(highlight_75, props='color:black;background-color: #e0ecf4;', axis=0, subset=slice2_)\
           .apply(highlight_0, props='color:black;background-color: #f7fcfd;', axis=0, subset=slice2_)\
           .set_table_styles([cell_hover, index_names])\
           .set_caption("{0}".format(init_time))
           # .format(make_clickable_test, escape="html", na_rep="NA", subset=slice_)
           # .format('<a href="#image" onclick="showImage("images/mclimate/ivt_mclimate_F6.png");">{0}</a>', escape="html", na_rep="NA")
    
           # .format(precision=0)\
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
"""
Filename:    heatmaps.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for creating a heatmap / table visualizing maximum percentile ranks for a given domain.
"""
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import textwrap

from datetime import timedelta

from plotting.configs import PLOT_CONFIG, HEATMAP_ORDER, kw_ticklabels
import plotting.colorbars as ccmap

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

def create_mini_heatmap(ax, df, cmap_name, config_key, ytcklbl, xtcklbl):
    
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
    data = df[[config_key]].to_numpy()
    if config_key != "duration":
        data_lbls = create_heatmap_annotation_labels(data)
    else:
        data_lbls = True
        
    sns.heatmap(data, cbar=False, annot=data_lbls, cmap=cmap, norm=norm, linewidths=.5, ax=ax, 
                yticklabels=ytcklbl, xticklabels=[xtcklbl], fmt='')
    ax.xaxis.tick_top()
    ax.set(xlabel="", ylabel="")

    # rows_per_day = 4  # if 6-hourly
    # hlines = np.arange(rows_per_day, len(df), rows_per_day)
    # ax.hlines(hlines, color='k', lw=0.8, *ax.get_xlim())
    ax.hlines([3, 7, 11, 15, 19, 23, 27, 31, 35, 39], color='k', lw=0.8, *ax.get_xlim())
    plt.yticks(rotation=0)

    return ax
    
def plot_heatmap_panel(fig, gs, df, init_date):
    print("Plotting Heatmap")
    heatmap_axes = []

    ## create list of valid dates
    ts = pd.to_datetime(init_date, format="%Y%m%d%H")
    col2 = []
    date_lbl = []
    step_lst = df["lead_time"].tolist()
    for i, step in enumerate(step_lst):
        ts_valid = ts + timedelta(hours=step)
        HH = ts_valid.strftime('%H')
        if HH == '06':
            date_lbl.append(ts_valid.strftime('%b %d'))
        valid_str = ts_valid.strftime('%H UTC')
        txt = '{0} | F{1}'.format(valid_str, str(step).zfill(3))
        col2.append(txt)
        
    df.index = col2

    for i, config_key in enumerate(HEATMAP_ORDER):
        ax = fig.add_subplot(gs[1:-1, i])
        heatmap_axes.append(ax)
        cfg = PLOT_CONFIG[config_key]
        cmap_name = cfg["cmap"]
        xtcklbl = cfg['label']

        if config_key == 'ivt':
            ytcklbl = df.index.values
        else:
            ytcklbl = False
        create_mini_heatmap(ax, df, 
                            cmap_name,
                            config_key,
                            ytcklbl,
                            xtcklbl)
        if i == 0:    
            rows_per_day = 4
            # lbl_loc = np.arange(
            #     rows_per_day / 2,
            #     len(df),
            #     rows_per_day
            # )
            lbl_loc = [1, 4.5, 8.5, 12.5, 16.5, 20.5, 24.5, 28.5, 32.5, 36.5]

            for j, datel in enumerate(date_lbl):
                ## add month day labels
                kw = {'weight': 'bold'}
                ax.text(-5., lbl_loc[j]+1.25, textwrap.fill(datel, width=3), va='bottom', ha='center',
                    rotation='horizontal', rotation_mode='anchor', **kw)

    return heatmap_axes
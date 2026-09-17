"""
Filename:    layout.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Function for creating the gridspec layout of the .png figure
"""

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.gridspec import GridSpec


def set_cw3e_font(current_dpi, scaling_factor, server='aware'):
    if server == 'aware':
        fm.fontManager.addfont('/cw3e/mead/projects/cwp140/repos/mclimate_tool_cw3e/utils/fonts/helvetica.ttc')
    else:
        fm.fontManager.addfont('/data/projects/operations/GEFS_Mclimate/utils/fonts/helvetica.ttc')

    plt.rcParams.update({
                    'font.family' : 'Helvetica',
                    'figure.dpi': current_dpi,
                    'font.size': 8 * scaling_factor, #changes axes tick label
                    'axes.labelsize': 8 * scaling_factor,
                    'axes.titlesize': 8 * scaling_factor,
                    'xtick.labelsize': 8 * scaling_factor,#do nothing
                    'ytick.labelsize': 8 * scaling_factor, #do nothing
                    'legend.fontsize': 5 * scaling_factor,
                    'lines.linewidth': 0.7 * scaling_factor,
                    'axes.linewidth': 0.2 * scaling_factor,
                    'legend.fontsize': 12 * scaling_factor,
                    'xtick.major.width': 0.8 * scaling_factor,
                    'ytick.major.width': 0.8 * scaling_factor,
                    'xtick.minor.width': 0.6 * scaling_factor,
                    'ytick.minor.width': 0.6 * scaling_factor,
                    'lines.markersize': 6 * scaling_factor
                })

def initialize_figure(server='aware'):

    # Create figure
    fig = plt.figure(figsize=(11.75, 14.))
    fig.dpi = 300
    fmt = 'png'

    base_dpi=100
    scaling_factor = (fig.dpi/ base_dpi)**0.3

    set_cw3e_font(fig.dpi, scaling_factor, server)
    
    nrows = 9
    ncols = 8

    ## Use gridspec to set up a plot with a series of subplots that is
    ## n-rows by n-columns
    gs = GridSpec(nrows, ncols, 
                  height_ratios=[0.05, 0.45, 0.05, 0.05, 0.5, 0.05, 0.05, 1, 0.05],
                  width_ratios = [0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 1, 1], 
                  wspace=0.05, 
                  hspace=0.15)

    ## use gs[rows index, columns index] to access grids

    return fig, gs


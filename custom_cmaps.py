"""
Filename:    custom_cmaps.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for custom cmaps adapted from from https://github.com/samwisehawkins/nclcmaps
"""

import numpy as np
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap


__all__ = ['custom_cmaps']

custom_cmaps =    {
                "mclimate_green" :{ 
                        "colors":[[1.000, 1.000, 0.898], # 75 - 90
                            [0.969, 0.988, 0.725], # 90 - 94
                            [0.851, 0.941, 0.639], # 94 - 95
                            [0.678, 0.867, 0.557], # 95 - 96
                            [0.471, 0.776, 0.475], # 96 - 97
                            [0.255, 0.671, 0.365], # 97 - 98
                            [0.137, 0.518, 0.263], # 98 - 99
                            [0.000, 0.408, 0.216], # 99 - 100
                            [0.000, 0.271, 0.161]], # 100 - 101.
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": 'Model Climate Percentile Rank (xth)',
                        },
    
                "mclimate_purple" :{
                        "colors":[
                            [0.878, 0.925, 0.957],  # 0. - 75
                            [0.749, 0.827, 0.902], # 75 - 90
                            [0.620, 0.737, 0.855], # 90 - 95
                            [0.549, 0.588, 0.776], # 95 - 97
                            [0.549, 0.420, 0.694], # 97 - 99
                            [0.533, 0.255, 0.616], # 99 - 99.5
                            [0.506, 0.059, 0.486], # 99.5 - 99.8
                            [0.302, 0.000, 0.294], # 99.8 - 99.9
                            [0.000, 0.000, 0.000]], # 99.9 - 100.
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": 'Model Climate Percentile Rank (xth)',
                        },
            "mclimate_red" :{
                        "colors":[
                            [255,255,204],
                            [255,237,160],
                            [254,217,118],
                            [254,178,76],
                            [253,141,60],
                            [252,78,42],
                            [227,26,28],
                            [189,0,38],
                            [128,0,38]],
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": 'Model Climate Percentile Rank (xth)',
                        }
}

def cmap(cbarname):
        data = np.array(custom_cmaps[cbarname]["colors"])
        data = data / np.max(data)
        cmap = ListedColormap(data, name=cbarname)
        bnds = custom_cmaps[cbarname]["bounds"]
        norm = mcolors.BoundaryNorm(bnds, cmap.N)
        cbarticks = custom_cmaps[cbarname]["ticks"]
        cbarlbl = custom_cmaps[cbarname]["label"]
        return cmap, norm, bnds, cbarticks, cbarlbl
"""
Filename:    plotter.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for creating a four panel map with Mclimate ranks and a heatmap with maximum Mclimate rank within Southeast Alaska.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from plotting.layout import initialize_figure
from plotting.labels import format_forecast_titles, add_panel_label, add_annotation_text, panel_label
from plotting.heatmaps import plot_heatmap_panel
from plotting.maps import plot_variable_panel

from utils import globalvars

path_to_data = globalvars.path_to_data
  
def save_figure(
    fig,
    domain_name,
    init_date,
    lead_time,
    out_root="output/images/mclimate/v1/GEFS_50",
    dpi=300,
    filetype="png",
):
    """
    Save figure to output directory.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure object to save
    domain_name : str
        Domain name (e.g. 'SEAK')
    init_date : str
        Initialization date (e.g. '2026010100')
    lead_time : int
        Lead time 
    out_root : str, optional
        Root output directory
    dpi : int, optional
        Output resolution
    filetype : str, optional
        File extension (png, pdf, jpg)
    """

    out_dir = Path(out_root) / domain_name / init_date / "1"
    out_dir.mkdir(parents=True, exist_ok=True)

    fname = out_dir / f"mclimate__v1__GEFS_50__{domain_name}__{init_date}__1__F{lead_time:03d}.{filetype}"

    print(f"Saving figure: {fname}")

    fig.savefig(
        fname,
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
    )

    return fname

def create_mclimate_figure(ds,
    fc,
    df,
    domain_name,
    domain_cfg,
    init_date,
    lead_time,
    panel_labels=False,
                          ):
    
    fig, gs = initialize_figure()

    labels = format_forecast_titles(domain_cfg, init_date, lead_time)

    ## plot heatmap
    heatmap_axes = plot_heatmap_panel(fig, gs, df, init_date)
    ## plot heatmaptxt
    add_annotation_text(fig, 
                        gs_loc=gs[-1, :5], 
                        txt=labels["heatmap"], 
                        wrap_length=30, 
                        xytext=(-85,5))
    
    ## plot IVT map
    ivt_ax = plot_variable_panel(
        fig=fig,
        gs_loc=gs[0:2,6], 
        domain_cfg=domain_cfg, 
        lats_lbl=True, 
        ds=ds, 
        fc=fc, 
        lead_time=lead_time, 
        config_key="ivt",
        cax=gs[2,6],
        title=labels["left"])

    ## plot freezing level map
    fl_ax = plot_variable_panel(
        fig=fig,
        gs_loc=gs[0:2,7], 
        domain_cfg=domain_cfg, 
        lats_lbl=False, 
        ds=ds, 
        fc=fc, 
        lead_time=lead_time, 
        config_key="freezing_level",
        cax=gs[2,7],
        title=labels["right"])

    ## plot UV map
    uv_ax = plot_variable_panel(
        fig=fig,
        gs_loc=gs[4:5,6], 
        domain_cfg=domain_cfg, 
        lats_lbl=True, 
        ds=ds, 
        fc=fc, 
        lead_time=lead_time, 
        config_key="uv",
        cax=gs[5,6],
        title=None)

    ## plot QPF map
    qpf_ax = plot_variable_panel(
        fig=fig,
        gs_loc=gs[4:5,7], 
        domain_cfg=domain_cfg, 
        lats_lbl=False, 
        ds=ds, 
        fc=fc, 
        lead_time=lead_time, 
        config_key="qpf",
        cax=gs[5,7],
        title=None)

    ## plot AR hazard map
    haz_ax = plot_variable_panel(
        fig=fig,
        gs_loc=gs[7,6:], 
        domain_cfg=domain_cfg, 
        lats_lbl=True, 
        ds=ds, 
        fc=fc, 
        lead_time=lead_time, 
        config_key="ar_index",
        cax=gs[8, 6:],
        title=None)
    
    # ## plot arhazard_txt
    add_annotation_text(fig, 
                        gs_loc=gs[6, 6:], 
                        txt=labels["arhazard"], 
                        wrap_length=101, 
                        xytext=(0, -24))

    ## add optional panel labels
    panel_configs = {
        "heatmap": {"ax": heatmap_axes[0], "x": -1.25, "y": 1.025},
        "ivt":     {"ax": ivt_ax, "x": 0.02, "y": 0.97},
        "fl":      {"ax": fl_ax, "x": 0.02, "y": 0.97},
        "uv":      {"ax": uv_ax, "x": 0.02, "y": 0.97},
        "qpf":     {"ax": qpf_ax, "x": 0.02, "y": 0.97},
        "haz":     {"ax": haz_ax, "x": 0.01, "y": 0.98},
    }
    
    if panel_labels:
        for i, cfg in enumerate(panel_configs.values()):
            add_panel_label(cfg["ax"], panel_label(i), x=cfg["x"], y=cfg["y"])
    
    save_figure(fig, domain_name, init_date, lead_time)
    plt.close(fig)
"""
Filename:    main.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Main driver for AR hazard processing.
Compute + save
→ AR index
→ save nc
→ save csv
Domain here is used to limit preprocessing of dataset as well as for information on the bounding box on the csv. 
"""

import argparse
import yaml
import pandas as pd
import time
from concurrent.futures import ProcessPoolExecutor

from reader import grib_helper
from reader.forecast_processor import process_all_variables
from ar_hazard.ar_hazard_index import compute_AR_hazard_index
from reader.io_utils import save_processed_datasets
from utils import globalvars


# ---------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--init-date",
    required=True,
    help="Initialization date YYYYMMDDHH",
)

parser.add_argument(
    "--source",
    default="reforecast",
    help="reforecast, realtime, or archive",
)

parser.add_argument(
    "--server",
    default="aware",
)

args = parser.parse_args()

init_date = args.init_date
source = args.source
server = args.server
globalvars.configure(server)

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

var_lst = [
    "qpf",
    "ivt",
    "freezing_level",
    "uv",
]

nworkers = 8

domain = {
    "lon_min": -179.5,
    "lon_max": -110.,
    "lat_min": 10.,
    "lat_max": 70.,
}


# ---------------------------------------------------------
# Build index files if reading realtime .grb2 files
# ---------------------------------------------------------
def make_index(lead_time):
    t0 = time.perf_counter()

    grib_helper.build_and_save_index_files(
        F=lead_time,
        init_date=init_date,
    )

    elapsed = time.perf_counter() - t0

    return lead_time, elapsed
        
if source == "realtime":  
    t00 = time.perf_counter()
    
    with ProcessPoolExecutor(max_workers=nworkers) as executor:
        results = list(
            executor.map(
                make_index,
                globalvars.qpf_leads,
            )
        )
    
    total = time.perf_counter() - t00
    
    print("\nIndividual times:")
    for F, elapsed in results:
        print(f"F{F:03d}: {elapsed:.2f} s")
    
# ---------------------------------------------------------
# Process variables
# ---------------------------------------------------------
t00 = time.perf_counter()
fc, final_ds = process_all_variables(
    init_date=init_date,
    var_lst=var_lst,
    domain=domain,
    source=source,
    server=server,
)


# ---------------------------------------------------------
# Compute AR hazard index
# ---------------------------------------------------------

final_ds = compute_AR_hazard_index(
    final_ds
)

# ---------------------------------------------------------
# Export netCDFs
# ---------------------------------------------------------

save_processed_datasets(
    fc,
    final_ds,
    init_date,
    source,
)

total = time.perf_counter() - t00
print(f"\nTotal time to read and preprocess data: {total:.2f} s")
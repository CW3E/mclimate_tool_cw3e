"""
Create plots from saved diagnostics.
Load + visualize
load nc
→ plot
"""
## code to plot faster
import matplotlib as mpl
mpl.use('agg')

import argparse
import yaml
import time
from concurrent.futures import ProcessPoolExecutor

from reader.io_utils import load_processed_datasets
from ar_hazard.summaries import export_summary_csv, load_summary_csv
from plotting.plotter import create_mclimate_figure
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
    "--domain",
    default="San-Mateo",
)

parser.add_argument(
    "--source",
    default="reforecast",
)

parser.add_argument(
    "--server",
    default="aware",
)

args = parser.parse_args()

init_date = args.init_date
domain_name = args.domain
source = args.source
server = args.server
globalvars.configure(server)

# ---------------------------------------------------------
# Domain config
# ---------------------------------------------------------

with open(
    "config/domain.yaml",
    "r",
) as f:

    config = yaml.safe_load(f)

domain_cfg = (
    config["domains"][domain_name]
)


# ---------------------------------------------------------
# Load processed datasets
# ---------------------------------------------------------

fc, final_ds = (
    load_processed_datasets(
        init_date=init_date,
        source=source,
    )
)

# ---------------------------------------------------------
# Export CSV
# ---------------------------------------------------------

export_summary_csv(
    final_ds,
    domain_name,
    domain_cfg,
    init_date,
    mode="max",
)

# ---------------------------------------------------------
# Import CSV
# ---------------------------------------------------------
df = load_summary_csv(
    domain_name=domain_name,
    init_date=init_date,
)

fc.load()
final_ds.load()

# ---------------------------------------------------------
# Create plots
# ---------------------------------------------------------

def make_plot(lead_time):
    t0 = time.perf_counter()

    create_mclimate_figure(
        ds=final_ds,
        fc=fc,
        df=df,
        domain_name=domain_name,
        domain_cfg=domain_cfg,
        init_date=init_date,
        lead_time=lead_time,
        panel_labels=True,
    )

    elapsed = time.perf_counter() - t0

    return lead_time, elapsed


t00 = time.perf_counter()

with ProcessPoolExecutor(max_workers=8) as executor:
    results = list(
        executor.map(
            make_plot,
            globalvars.leads,
        )
    )

total = time.perf_counter() - t00

print("\nIndividual times:")
for F, elapsed in results:
    print(f"F{F:03d}: {elapsed:.2f} s")

print(f"\nTotal plotting time: {total:.1f} seconds")
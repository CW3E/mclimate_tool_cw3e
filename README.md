## GFS MClimate Tool

---

This repository runs calculations and plots for the AR Impact Tool. Plot types include IVT M-Climate and Freezing Level M-Climate for GEFS.

Current capabilities include the Southeast Alaska region.

### To run:

---

To run all three regions with a singularity container:

```bash
## runs plots for GEFS
singularity exec --bind /data:/data,/home:/home,/work:/work,/common:/common -e /data/projects/containers/ar_landfall_tool/ar_landfall_tool.sif /opt/conda/bin/python /data/projects/operations/mclimate_tool/run_tool.py
## GFS MClimate Tool

---

This repository runs calculations and plots for the GFS Mclimate Tool. Plot types include IVT Mclimate and Freezing Level Mclimate for GFS.

Current capabilities include the Southeast Alaska region.

### To run:

---

To run all three regions with a singularity container:

```bash
## runs plots for GEFS
singularity exec --bind /data:/data,/home:/home,/work:/work,/common:/common -e /data/projects/containers/ar_landfall_tool/ar_landfall_tool.sif /opt/conda/bin/python /home/cw3eit/ARPortal/gefs/scripts/mclimate_tool_cw3e/run_tool.py
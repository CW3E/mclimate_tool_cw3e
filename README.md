## AR Impact Tool | GFS Model Climate

---

This repository runs calculations and plots for the AR Impact Tool. Plot types include IVT Model Climate (M-Climate) and Freezing Level M-Climate for GEFS.

Current capabilities include the Southeast Alaska region.

### To run:

---

To run all three regions with a singularity container:

```bash
## runs plots for GEFS
singularity exec --bind /data:/data,/home:/home,/work:/work,/common:/common -e /data/projects/operations/GEFS_Mclimate/envs/GEFS_Mclimate.sif /opt/conda/bin/python /data/projects/operations/GEFS_Mclimate/run_tool.py
```

## References
---
**Deanna L. Nash, Jonathan J. Rutz, Aaron Jacobs, and Brian Kawzenuk**
> Nash, Deanna, Rutz, J.J., Jacobs, A., and Kawzenuk, B. (2024). “Differentiating between impactful and non-impactful Atmospheric River events in Southeast Alaska”. In: <em>Journal of Operational Meteorology</em>  (in preparation)

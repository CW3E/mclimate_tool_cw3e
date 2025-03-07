#!/bin/bash

date=`date`
echo "STARTING AT "$date

lag=4
yyyy=`date -d '-'$lag' hours' -u +%Y`
mm=`date -d '-'$lag' hours' -u +%m`
dd=`date -d '-'$lag' hours' -u +%d`
hh=`date -d '-'$lag' hours' -u +%H`


echo "Running GEFS MClimate for "$yyyy $mm $dd $hh
rm -f /data/projects/operations/GEFS_Mclimate/figs/images_operational/*.png
cd /data/projects/operations/GEFS_Mclimate/

filename="/data/projects/derived_products/GEFS_IVT/data/GEFS_IVT_"$yyyy$mm$dd$hh".nc"
while true; do
  if [[ -e "$filename" ]]; then                   # Check if the file exists
    filesize1=$(stat --format="%s" "$filename")   # Get the file size
    sleep 5                                      # Wait a few seconds
    filesize2=$(stat --format="%s" "$filename")   # Get the file size again

    if [[ "$filesize1" == "$filesize2" ]]; then  # Compare file sizes
      break                                      # Exit the loop if file size is not changing
    else
      echo $filename" is still being written (file size is changing)."
      sleep 30
    fi
  else
    echo $filename" does not exist."
    sleep 30
  fi
done

echo $filename" ready for processing"

date=`date`
echo "STARTING MAKING PRODUCTS at "$date

/bin/singularity exec --bind /data:/data,/home:/home,/work:/work,/common:/common -e /data/projects/operations/GEFS_Mclimate/envs/GEFS_Mclimate.sif /opt/conda/envs/container/bin/python /data/projects/operations/GEFS_Mclimate/run_tool.py "$yyyy$m$dd$hh"

cd /data/projects/operations/GEFS_Mclimate/figs/images_operational/
try=1
while [ $try -le 5 ]; do
 timeout 240 rsync --ignore-missing-args -avih *.png /data/projects/website/mirror/htdocs/Projects/MClimate/images/images_operational/
 if [ $? -eq 0 ]; then
  break
 fi
 attempt=$((attempt + 1))
 sleep 5
done


exit




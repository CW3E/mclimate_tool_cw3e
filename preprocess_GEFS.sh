#!/bin/bash
######################################################################
# Filename:    preprocess_GEFS.sh
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to copy GEFS .grb2 files over to temporary, then extract freezing level and UV1000 to .nc files
#
######################################################################

## get the latest directory
DATADIR=$(ls -td /data/projects/external_datasets/GEFS/processed/*/ | head -1)
## directory to copy files to 
OUTDIR="/data/projects/Comet/cwp140/"

## copy files every 6 hours from DATADIR to OUTDIR
for i in $(seq -f "%03g" 6 6 168)
do
  fname="gefs_*_F${i}.grb2"
  infile=${DATADIR}${fname}
  echo $infile
  cp $infile $OUTDIR
done



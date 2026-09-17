#!/bin/bash

DATE="2026091406"

python main.py --init-date "$DATE" --source "realtime" --server "aware"
 
python main_plot.py --init-date "$DATE" --domain "NPAC" --source "realtime" --server "aware"

python main_plot.py --init-date "$DATE" --domain "SEAK" --source "realtime" --server "aware"


exit




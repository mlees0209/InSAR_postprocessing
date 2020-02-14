#!/bin/bash

# USEAGE: check_times_LO.sh DIRECTORY_CONTAINING_SAFE_FILES
# where SAFE_FILES are unzipped .SAFE sentinel folders.
#
# This script naively takes the names of the unzipped SAFE folders and visualises them.

echo "USEAGE: check_times_LO.sh DIRECTORY_CONTAINING_SAFE_FILES"

dir=$1
echo -e "Getting times from "$dir.
currentdir=$(pwd)
ls -d $dir/*.SAFE > names.tmp
rev names.tmp | cut -d"/" -f1 | rev | cut -d"_" -f6 | cut -f1 -d"T" > dates.tmp

echo -e "Executing Python script:"
cmd="python pythonsubroutines/make_dates.py "$dir" "$currentdir
echo -e '	'$cmd
python /Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/python_subroutines/plot_dates.py $dir $currentdir

echo -e 'Tidying up...'
rm *.tmp

open $currentdir/L0_timeseries.png
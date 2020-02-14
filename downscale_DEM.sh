#!/bin/bash

### This script takes a Drummer produced .dem and .dem.rsc files, and creates a new DEM over the same region with the specified coarser resolution.
#
# Usage: Visualise_DEM olddemfilename newdemfilename newnolats newnolons 	

binary_dem_filename=$1
outputname=$2
newnolats=$3
newnolons=$4


minlat=$(awk '{print $2}' $binary_dem_filename.rsc | sed -n '4p')
nolats=$(awk '{print $2}' $binary_dem_filename.rsc | sed -n '2p')
deltalat=$(awk '{print $2}' $binary_dem_filename.rsc | sed -n '6p')
DelLat=`gmt math -Q $nolats $deltalat MUL =`
maxlat=`gmt math -Q $minlat $DelLat ADD =`

minlon=$(awk '{print $2}' $binary_dem_filename.rsc | sed -n '3p')
nolons=$(awk '{print $2}' $binary_dem_filename.rsc | sed -n '1p')
deltalon=$(awk '{print $2}' $binary_dem_filename.rsc | sed -n '5p')
DelLon=`gmt math -Q $nolons $deltalon MUL =`
maxlon=`gmt math -Q $minlon $DelLon ADD =`

maxlon=$(printf "%.3f" $maxlon) # round to 3dp, presuming you didn't define it any finer than that
maxlat=$(printf "%.3f" $maxlat) # ditto

reg="-R"$minlon"/"$maxlon"/"$maxlat"/"$minlat
echo -e "Region of original (and final) DEM is "$reg

echo -e "Making the .nc gridded version of "$binary_dem_filename"."
origsize=$(ls -l -h $binary_dem_filename | awk '{print $5}')
echo -e "	File "$binary_dem_filename" is "$origsize" large. Are you sure you want to do this? (may take bloody ages)"
echo "	Do that? [Y,n]"
read input
if [[ $input == "Y" || $input == "y" ]]; then
	deltalat=$(gmt math -Q $deltalat -1 MUL =)
	gmt xyz2grd $binary_dem_filename -Gbiggrid.nc.tmp -I$nolons+/$nolats+ $reg -ZTLh -V
else
        echo "	Moving on to the next step, assuming the grid already exists (if it doesn't you'll get nothing but errors now)"
fi
echo -e " "

gmt grdsample biggrid.nc.tmp -G$outputname.nc.tmp -I$newnolons+/$newnolats+ $reg -V

gmt grd2xyz $outputname.nc.tmp -ZTLh -V > $outputname

rm *.tmp
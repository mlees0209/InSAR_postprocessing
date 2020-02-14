#!/bin/bash

# This script takes a binary dem created on the Drummer machines (eg step0_create_dem.py) and
# converts it into a georeferenced kml image to look at in Google Earth. You need the .dem and
# .dem.rsc files from the drummer scripts and the rest works for you. Two kml's are outputted,
# 'topo.kml' which is the Drummer topo and 'topo_GMT.kml' which is the GMT topo over the same region.

# USAGE: ./Master_Script_binary ELEVATION.dem

### Input variables here
binary_dem_filename=$1

### MAIN SCRIPT: edit at your PERIL!!!

echo -e "I'm going to run the Python script quietly for a few moments..."
python3 DEM_converter.py $binary_dem_filename
echo -e "	Python Script Done!"

proj="-JX5i"
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

reg="-R"$minlon"/"$maxlon"/"$maxlat"/"$minlat
echo "Region of DEM is "$reg

xyzfilename=$(cat outputname.tmp)
echo -e "xyzfilename = "$xyzfilename

echo -e "Gridding the xyz data, have a bit of paitence"

gmt xyz2grd $xyzfilename -Gtopotest.nc $reg -I$nolons+/$nolats+ -Vv -bi3f
gmt grdgradient topotest.nc -Ne0.8 -A100 -fg -Gillumination.nc # makes a perspective image
gmt grd2cpt topotest.nc -Crelief -Z > colours.cpt
#gmt grdimage topotest.nc $proj -Ccolours.cpt -Iillumination.nc > topotest.ps # plot the topography
gmt grdimage topotest.nc $proj -Ccolours.cpt > topotest.ps # plot the topography

gmt psconvert topotest.ps -TG -W+k+t"topo_insar"+l256/-1

gmt psconvert topotest.ps -A -P -Tf
open topotest.pdf


# Now make a 'correct' topography map

gmt grdcut ftp://ftp.soest.hawaii.edu/gmt/data/earth_relief_15s.grd $reg -Gtopo_gmt.nc # gets a detailed topo grid
gmt grd2cpt topo_gmt.nc -Crelief -Z > colours_gmt.cpt
gmt grdgradient topo_gmt.nc -Ne0.8 -A100 -fg -Gillumination_gmt.nc # makes a perspective image
#gmt grdimage topo_gmt.nc $proj -Ccolours_gmt.cpt -Iillumination_gmt.nc > topo_gmt.ps # plot the topography
gmt grdimage topo_gmt.nc $proj -Ccolours_gmt.cpt > topo_gmt.ps # plot the topography

gmt psconvert topo_gmt.ps -TG -W+k+t"topo_gmt"+l256/-1

gmt psconvert topo_gmt.ps -A -P -Tf
open topo_gmt.pdf

rm *.tmp
rm colours*

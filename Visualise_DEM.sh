#!/bin/bash

### This script takes a Drummer produced .dem and .dem.rsc files, and creates:
#		1. a basic image (png) map showing the DEM.
#		2. a .kml which projects the png map for viewing in Google Earth.
#		3. a .nc gridded version of the DEM (this is really a byproduct).
#
# Usage: Visualise_DEM demfilename	where demfilename is 'NAME.dem'.

echo "Visualise_anything.sh usage: visualise_anything binary_dem_filename. Any other usage and it won't work."


binary_dem_filename=$1

proj=-JX15i

outputname=$(echo $binary_dem_filename | rev | cut -d'/' -f1 | rev)

# Set pen for gridlines and other visual parameters
gmt set MAP_GRID_PEN_PRIMARY 0.2p,black,-
gmt set FONT_LABEL 5p
gmt set FONT_ANNOT_PRIMARY 5p
gmt set PS_MEDIA A2


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

# work out grid line spacing to give us 3 horizonal and 3 vertical line. Unfinished, currently only works for square maps. Also unusued....
gridspacelat=`gmt math -Q $DelLat -3 DIV =`
gridspacelat=$(printf "%.1f" $gridspacelat) # ditto
echo "Gridspacing is "$gridspacelat


reg="-R"$minlon"/"$maxlon"/"$maxlat"/"$minlat
echo -e "Region of DEM is "$reg

echo -e "Making the .nc gridded version of "$binary_dem_filename"."
origsize=$(ls -l -h $binary_dem_filename | awk '{print $5}')
echo -e "	File "$binary_dem_filename" is "$origsize" large. Are you sure you want to do this? (may take bloody ages)"
echo "	Do that? [Y,n]"
read input
if [[ $input == "Y" || $input == "y" ]]; then
	deltalat=$(gmt math -Q $deltalat -1 MUL =)
	gmt xyz2grd $binary_dem_filename -G$outputname.nc -I$nolons+/$nolats+ $reg -ZTLh -V
else
        echo "	Moving on to the next step, assuming the grid already exists (if it doesn't you'll get nothing but errors now)"
fi
echo -e " "


echo -e "Making cmap."
gmt grd2cpt $outputname.nc -Cglobe -T= -E100nlevels -V > shades.cpt.tmp

echo -e "Making image and map."

gmt grdimage $outputname.nc $proj -Cshades.cpt.tmp -E600 -Q --MAP_FRAME_TYPE=inside -K > $outputname.ps
gmt psbasemap $proj $reg -BWSne -Bxyag -V -O -K --MAP_FRAME_TYPE=inside >> $outputname.ps
gmt psscale -DjTL+w2i/0.15i+h+o0.1i -Baf -F+gwhite@20 -R -J -N300 -Cshades.cpt.tmp -O >> $outputname.ps

gmt psconvert $outputname.ps -TG -W+k+t"Drummer DEM"+l256/-1 -V

echo -e "Removing temporary and ps files..."
rm *.tmp
rm *.ps
echo -e "...Done..."

open $outputname.png
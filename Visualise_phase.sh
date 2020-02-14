#!/bin/bash

# This script takes a Drummer-produced Single Look Complex (SLC) in phase form (.geo.phase ; convert to phase using Python), in combination with a dem .rsc file, and produces:
#		1. a basic image (png) map showing the phase of the SLC.
#
# Usage: Visualise_SLC slcfilenam demfilename		where slcfilename is 'NAME.geo.phase' (having been put into phase previously).

slcfilename=$1
pathlength=$(tr -dc '/' <<< $slcfilename | wc -c | tr -d ' ')
#demfilename=$(echo $slcfilename | cut -d '/' -f 1-$pathlength)"/elevation.dem.rsc"
#demfilename='drummer16/pepin/cv_asc/elevation_interp_us.dem.rsc'
demfilename=$2

geofiletag=$(echo $slcfilename | rev | cut -d '/' -f1 | rev)
echo -e ".geo filename is "$geofiletag
echo -e "DEM filename guessed to be "$demfilename". If this isn't right then it'll all go to shit." 

proj=-JX15i

# Set pen for gridlines and other visual parameters
gmt set MAP_GRID_PEN_PRIMARY 0.2p,black,-
gmt set FONT_LABEL 8p
gmt set FONT_ANNOT_PRIMARY 8p
gmt set PS_MEDIA A2


minlat=$(awk '{print $2}' $demfilename | sed -n '4p')
nolats=$(awk '{print $2}' $demfilename | sed -n '2p')
deltalat=$(awk '{print $2}' $demfilename | sed -n '6p')
DelLat=`gmt math -Q $nolats $deltalat MUL =`
maxlat=`gmt math -Q $minlat $DelLat ADD =`

minlon=$(awk '{print $2}' $demfilename | sed -n '3p')
nolons=$(awk '{print $2}' $demfilename | sed -n '1p')
deltalon=$(awk '{print $2}' $demfilename | sed -n '5p')
DelLon=`gmt math -Q $nolons $deltalon MUL =`
maxlon=`gmt math -Q $minlon $DelLon ADD =`

maxlon=$(printf "%.3f" $maxlon) # round to 3dp, presuming you didn't define it any finer than that
maxlat=$(printf "%.3f" $maxlat) # ditto


reg="-R"$minlon"/"$maxlon"/"$maxlat"/"$minlat
echo -e "	Region of guessed DEM (therefore SLC) is "$reg". Hopefully this is right!"

echo -e "Making the .nc gridded version of "$slcfilename"."
origsize=$(ls -l -h $slcfilename | awk '{print $5}')
echo -e "	File "$slcfilename" is "$origsize" large. Are you sure you want to do this? (may take bloody ages; above 2 GB you are talking like 10 minutes of waiting time...)"
echo "	Do that? [Y,n]"
read input
if [[ $input == "Y" || $input == "y" ]]; then
        deltalat=$(gmt math -Q $deltalat -1 MUL =)
		gmt xyz2grd $slcfilename -G$slcfilename.nc -I$nolons+/$nolats+ $reg -ZTLf -Vl

else
        echo "	Moving on to the next step, assuming the grid already exists (if it doesn't you'll get nothing but errors now)"
fi
echo -e " "


gmt grd2cpt $slcfilename.nc -Cgray -L-3.15/3.15 -S20 -V > shades.cpt.tmp

echo -e "Making image and map."
gmt grdimage $slcfilename.nc $proj -Cshades.cpt.tmp -E600 -Q --MAP_FRAME_TYPE=inside -K -V > $geofiletag.ps
gmt psbasemap $proj $reg -BWSne -Bxyag -V -O -K --MAP_FRAME_TYPE=inside >> $geofiletag.ps
echo $geofiletag | gmt pstext $proj $reg -F+cTR+f12,white -Gblack@60 -D-0.2/-0.2 -P -O -K >> $geofiletag.ps
gmt psscale -DjTL+w2i/0.15i+h+o0.1i -Baf -F+gwhite@40 -R -J -N300 -Cshades.cpt.tmp -O >> $geofiletag.ps


gmt psconvert $geofiletag.ps -TG -W+k+t"SLC"+l256/-1 -V

echo -e "Removing temporary and ps files..."
rm *.tmp
rm *.ps
echo -e "...Done..."

open $geofiletag.png

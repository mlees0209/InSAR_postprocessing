#!/bin/bash

# Visualises a stack, which is a text file containing headings: Latitude, Longitude and Velocity (amongst other optional additional headings). You need a corresponding .dem.rsc file for this to work! 

echo "Visualise_stack.sh usage: visualise_stack FILE_TO_PLOT DEM.RSC_FILE. Any other usage and it won't work."

toplotfilename=$1
demfilename=$2

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

vellinenum=$(head -1 $toplotfilename | tr ' ' '\n' | grep -n "Velocity" | tr -d ':Velocity')
vellinenum=$(( $vellinenum - 1 ))
echo "Velocity line number is "$vellinenum

latlinenum=$(head -1 $toplotfilename | tr ' ' '\n' | grep -n "Latitude" | tr -d ':Latitude')
latlinenum=$(( $latlinenum - 1 ))
echo "Latitude line number is "$latlinenum


lonlinenum=$(head -1 $toplotfilename | tr ' ' '\n' | grep -n "Longitude" | tr -d ':Longitude')
lonlinenum=$(( $lonlinenum - 1 ))
echo "Longitude line number is "$lonlinenum



reg="-R"$minlon"/"$maxlon"/"$maxlat"/"$minlat
echo -e "	Region of guessed DEM is "$reg". Hopefully this is right!"

echo -e "Making the .nc gridded version of "$toplotfilename"."
origsize=$(ls -l -h $toplotfilename | awk '{print $5}')
echo -e "	File "$toplotfilename" is "$origsize" large. Are you sure you want to do this? (may take bloody ages)"
echo "	Do that? [Y,n]"
read input
if [[ $input == "Y" || $input == "y" ]]; then
        deltalat=$(gmt math -Q $deltalat -1 MUL =)
		gmt xyz2grd $toplotfilename -G$toplotfilename.nc.tmp -h1 -I$nolons+/$nolats+ $reg -i$lonlinenum,$latlinenum,$vellinenum -Vl

else
        echo "	Moving on to the next step, assuming the grid already exists (if it doesn't you'll get nothing but errors now)"
fi
echo -e " "


gmt grd2cpt $toplotfilename.nc.tmp -Cred2green -Ic -T= -V > shades.cpt.tmp # -Ic reverses direction of colours. -T= makes symmetric.

echo -e "Making image and map."
gmt grdimage $toplotfilename.nc.tmp $proj -Cshades.cpt.tmp -E600 -Q --MAP_FRAME_TYPE=inside -K -V > $toplotfilename.ps
gmt psbasemap $proj $reg -BWSne -Bxyag -V -O -K --MAP_FRAME_TYPE=inside >> $toplotfilename.ps
echo $toplotfilename | gmt pstext $proj $reg -F+cTR+f12,white -Gblack@60 -D-0.2/-0.2 -P -O -K >> $toplotfilename.ps
gmt psscale -DjTL+w2i/0.15i+h+o0.1i -Baf -F+gwhite@40 -R -J -N300 -Cshades.cpt.tmp -O >> $toplotfilename.ps

gmt psconvert $toplotfilename.ps -TG -W+k+t$toplotfilename+l256/-1 -V

echo -e "Removing temporary and ps files..."
rm *.tmp
rm *.ps
echo -e "...Done..."

open $toplotfilename.png
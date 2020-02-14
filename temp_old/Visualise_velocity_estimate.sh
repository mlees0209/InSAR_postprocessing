#!/bin/bash

# This script takes Drummer directory containing interferograms, makes a linear velocity estimate and plots it.
#
# Usage: Visualise_mean_correlation directory		where directory is the path to the folder containing the interferograms (.u and .cc files) and also a .dem.rsc file.

echo "Visualise_velocity_estimate.sh usage: visualise_velocity_estimate FILE_TO_PLOT DEM.RSC_FILE. Any other usage and it won't work."

directory=$1
python /Users/mlees/Documents/RESEARCH/InSAR_processing/postprocessing_scripts/python_subroutines/create_linear_velocity_esimtate.py $directory

demfilename=$directory/dem.rsc

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
echo -e "	Region of guessed DEM is "$reg". Hopefully this is right!"

echo -e "Making the .nc gridded version of mean_coherence.txt."
origsize=$(ls -l -h mean_coherence.txt | awk '{print $5}')
echo -e "	File "$slcfilename" is "$origsize" large. Are you sure you want to do this? (may take bloody ages)"
echo "	Do that? [Y,n]"
read input
if [[ $input == "Y" || $input == "y" ]]; then
        deltalat=$(gmt math -Q $deltalat -1 MUL =)
		gmt xyz2grd mean_coherence.txt -Gmean_coherence.nc -I$nolons+/$nolats+ $reg -ZTLf -V

else
        echo "	Moving on to the next step, assuming the grid already exists (if it doesn't you'll get nothing but errors now)"
fi
echo -e " "


gmt grd2cpt mean_coherence.nc -Cgray -L0/1 -S20 -V > shades.cpt.tmp

echo -e "Making image and map."
gmt grdimage mean_coherence.nc $proj -Cshades.cpt.tmp -E600 -Q --MAP_FRAME_TYPE=inside -K -V > mean_coherence.ps
gmt psbasemap $proj $reg -BWSne -Bxyag -V -O -K --MAP_FRAME_TYPE=inside >> mean_coherence.ps
echo mean_coherence | gmt pstext $proj $reg -F+cTR+f12,white -Gblack@60 -D-0.2/-0.2 -P -O -K >> mean_coherence.ps
gmt psscale -DjTL+w2i/0.15i+h+o0.1i -Baf -F+gwhite@40 -R -J -N300 -Cshades.cpt.tmp -O >> mean_coherence.ps


gmt psconvert mean_coherence.ps -TG -W+k+t"mean coherence"+l256/-1 -V

echo -e "Removing temporary and ps files..."
rm *.tmp
rm *.ps
echo -e "...Done..."

open mean_coherence.png

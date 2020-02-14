#!/bin/bash

### This script plots the mean correalation of a big InSAR file. The result is a kml and a png. The scalebar is also outputted separately. If DEBUGFLAG is y, then temporary .tmp and .ps files are retained.

if [ "$#" -lt 3 ]; then
    echo "Useage: ./Visualise_Correlation_SBAS.sh InSARdata pixelsize outputname [debugflag]"
    exit 2
fi


InSARdata=$1
pixelsize=$2
outputname=$3
debugflag=$4

proj="-JX15ig" # the final 'g' tells GMT  that this is a linear, geographic projection
#proj='-JM5i'
gmt set PS_MEDIA A2
gmt set FONT_ANNOT_PRIMARY 16p
gmt set FONT_LABEL 20p

echo -e "Finding the range of the data."
reg=$(gmt info -h1 -Vl -I0.000001 -: $InSARdata)
echo "Range is given as "$reg


echo -e "\tFinding the last column of the InSARdata, and finding which column is mean correlation."
latlinenum=$(head -1 $InSARdata | tr ' ' '\n' | grep -n "Latitude" | tr -d ':Latitude')
latlinenum=$(( $latlinenum - 1 ))
echo "Latlinnum = "$latlinenum
lonlinenum=$(head -1 $InSARdata | tr ' ' '\n' | grep -n "Longitude" | tr -d ':Longitude')
lonlinenum=$(( $lonlinenum - 1 ))
echo "Lonlinenum = "$lonlinenum
corrlinenum=$(head -1 $InSARdata | tr ' ' '\n' | grep -n "Mean_Corr" | tr -d ':Mean_Corr')
corrlinenum=$(( $corrlinenum - 1 ))

echo "Meancorr linenum = "$corrlinenum

echo "Making the plotting file plotting.tmp"
nodataentries=$(gmt info $InSARdata -Fi | cut -f5)

yes $pixelsize | head -n $nodataentries > pixelsize.tmp

gmt convert -o$lonlinenum,$latlinenum,$corrlinenum -h1 $InSARdata > plotting.tmp

yes "0" | head -n $nodataentries > azimuth.tmp

paste plotting.tmp azimuth.tmp > plotting3.tmp
paste plotting3.tmp pixelsize.tmp > plotting2.tmp
paste plotting2.tmp pixelsize.tmp > plotting.tmp


echo -e "\tForming a map."
#gmt grdimage /Users/mlees/Documents/RESEARCH/bigdata/Google_Satellite_Imagery/SouthCentralValley_zoom10.tif $proj $reg -K -V > $outputname.ps # plot the topography
gmt psbasemap $reg $proj --MAP_FRAME_TYPE=inside -BSWne -Bxya -K > $outputname.ps # Plot the map frame.

gmt makecpt -Cred2green -T0/1 -M -V > colours.cpt.tmp # makes colours for InSAR.
gmt psxy $reg $proj plotting.tmp -Ccolours.cpt.tmp -SJ -t40 -V -O >> $outputname.ps

#gmt psscale -DjTL+w8i/0.3i+h+o0.5i -R -J -Baf -W-1 -Ccolours.cpt.tmp -F -B+l"Deformation / mm" -O >> $outputname.ps # to plot the old 2018 data use -W-1 to invert the data.

#gmt psconvert $outputname.ps -P -A -TG -W+g -Vl
gmt psconvert $outputname.ps -TG -E720 -Z -W+k+t$toplotfilename+l256/-1 

# Do a separate scalebar
echo "Making a separate colourbar with name colorbar.png. Will overwrite an existing file with that time."
gmt psscale -Ccolours.cpt.tmp -Dx8c/1c+w12c/0.5c+jTC+h -Bxaf+l"Correlation" -P > $outputname.colorbar.ps
gmt psconvert $outputname.colorbar.ps -Tg -A -Z

if [ -z "$debugflag" ]; then 
	echo "debugflag is unset; removing temporary files"
	rm *tmp*; 	
else 
	echo "debugflag is set to '$debugflag'; not deleting temp files"; 
fi


open $outputname.png
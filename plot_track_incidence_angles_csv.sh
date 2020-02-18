#!/bin/bash

### This script plots the track angle and incidence angle for one of Tom's csv files.
if [ "$#" -lt 3 ]; then
    echo "Useage: ./plot_track_incidence_angles_csv InSARdata pixelsize outputname [debugflag]"
    exit 2
fi

InSARdata=$1
pixelsize=$2
outputname=$3
debugflag=$4

myInvocation="$(printf %q "$BASH_SOURCE")$((($#)) && printf ' %q' "$@")"
echo "Command called was "$myInvocation" which is written in "$outputname".info."
echo -e "Command called was:" > $outputname.info
echo -e
echo "$myInvocation" >> $outputname.info

proj="-JX15ig" # the final 'g' tells GMT  that this is a linear, geographic projection
#proj='-JM5i'
gmt set PS_MEDIA A2
gmt set FONT_ANNOT_PRIMARY 16p
gmt set FONT_LABEL 20p

echo -e "\tFinding the last column of the InSARdata, and finding which column is lat/lon."

if grep -q "latitude" $InSARdata ; then
	echo 'things are going fine'
	else echo $InSARdata' does not have column latitude. Aborting!'
	exit 2; 
fi


latlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "latitude" | tr -d ':latitude')
latlinenum=$(( $latlinenum - 1 ))
echo "Latlinnum = "$latlinenum
lonlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "longitude" | tr -d ':longitude')
lonlinenum=$(( $lonlinenum - 1 ))
echo "Lonlinenum = "$lonlinenum
tracklinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "track angle" | tr -d ':track angle')
tracklinenum=$(( $tracklinenum - 1 ))
echo "Tracklinenum = "$tracklinenum
Incidencelinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "incidence angle" | tr -d ':incidence angle')
Incidencelinenum=$(( $Incidencelinenum - 1 ))
echo "Incidencelinenum = "$Incidencelinenum

echo -e "Finding the range of the data."
reg=$(gmt info -h1 -Vl -I0.000001 -i$lonlinenum,$latlinenum $InSARdata)
echo "Range is given as "$reg

echo "Making the plotting file plotting_track.tmp"
gmt convert -o$lonlinenum,$latlinenum,$tracklinenum -h1 $InSARdata > plotting_track.tmp
echo "Making the plotting file plotting_incidence.tmp"
gmt convert -o$lonlinenum,$latlinenum,$Incidencelinenum -h1 $InSARdata > plotting_incidence.tmp


echo -e "Making gridded versions."
gmt xyz2grd -G$outputname-track.nc -I$pixelsize $reg plotting_track.tmp -Dlon/lat
gmt xyz2grd -G$outputname-incidence.nc -I$pixelsize $reg plotting_incidence.tmp -Dlon/lat

echo -e "Making colourscales; it will automatically be symmetric about zero."
gmt grd2cpt $outputname-track.nc -Cseafloor -Z > colours_track.cpt.tmp
gmt grd2cpt $outputname-incidence.nc -Cviridis -Z > colours_incidence.cpt.tmp

echo -e "\tForming a coloured-point track map."
gmt psbasemap $reg $proj --MAP_FRAME_TYPE=inside -BSWne -Bxya -K > $outputname-track.ps # Plot the map frame.
gmt grdimage $outputname-track.nc $proj -Ccolours_track.cpt.tmp -Q -O >> $outputname-track.ps

echo -e "\tForming a coloured-point incidence map."
gmt psbasemap $reg $proj --MAP_FRAME_TYPE=inside -BSWne -Bxya -K > $outputname-incidence.ps # Plot the map frame.
gmt grdimage $outputname-incidence.nc $proj -Ccolours_incidence.cpt.tmp -Q -O >> $outputname-incidence.ps

gmt psconvert $outputname-incidence.ps -TG -E720 -W+k+t$toplotfilename+l256/-1
gmt psconvert $outputname-incidence.ps -TG -E720 -W+g
gmt psconvert $outputname-track.ps -TG -E720 -W+k+t$toplotfilename+l256/-1
gmt psconvert $outputname-track.ps -TG -E720 -W+g

# Do a scalebars
echo "Making colourbars."
gmt psscale -Ccolours_track.cpt.tmp -Dx8c/1c+w12c/0.5c+jTC+h -Bxaf+l"Track angle (deg)" -P > $outputname-track.colorbar.ps
gmt psconvert $outputname-track.colorbar.ps -Tg -A

gmt psscale -Ccolours_incidence.cpt.tmp -Dx8c/1c+w12c/0.5c+jTC+h -Bxaf+l"Incidence angle (deg)" -P > $outputname-incidence.colorbar.ps
gmt psconvert $outputname-incidence.colorbar.ps -Tg -A


if [ "$debugflag" = "y" ]; then 
	echo "debugflag is set to '$debugflag'; not deleting temp files"; 
else 
	echo "debugflag is unset; removing temporary files"
	rm *tmp*;
	rm *.ps; 	
fi

open $outputname.png

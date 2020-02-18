#!/bin/bash

### This script plots the contour map between two dates in an InSAR csv file. 
#


if [ "$#" -lt 3 ]; then
    echo "Useage: ./plot_contours_datepair InSARdata startdate enddate pixelsize outputname [debugflag]"
    exit 2
fi

InSARdata=$1
startdate=$2
enddate=$3
pixelsize=$4
contour_int=$5
outputname=$6
debugflag=$7

myInvocation="$(printf %q "$BASH_SOURCE")$((($#)) && printf ' %q' "$@")"
echo "Command called was "$myInvocation" which is written in "$outputname".info."
echo -e "Command called was:" > $outputname.info
echo "$myInvocation" >> $outputname.info

proj="-JX15ig" # the final 'g' tells GMT  that this is a linear, geographic projection
#proj='-JM5i'
gmt set PS_MEDIA A2
gmt set FONT_ANNOT_PRIMARY 16p
gmt set FONT_LABEL 20p

echo -e "\tFinding the relevant columns of the InSARdata."

if grep -q "Latitude" $InSARdata ; then
	echo 'things are going fine'
	else echo $InSARdata' does not have column Latitude. Aborting!'
	exit 2; 
fi


latlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "Latitude" | tr -d ':Latitude')
latlinenum=$(( $latlinenum - 1 ))
echo "Latlinnum = "$latlinenum
lonlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "Longitude" | tr -d ':Longitude')
lonlinenum=$(( $lonlinenum - 1 ))
echo "Lonlinenum = "$lonlinenum
startdatelinenum=$(~/InSAR_processing/postprocessing_scripts/python_subroutines/get_column_no_from_date.py $InSARdata $startdate)
enddatelinenum=$(~/InSAR_processing/postprocessing_scripts/python_subroutines/get_column_no_from_date.py $InSARdata $enddate)
echo "startdatelinenum = "$startdatelinenum
echo "enddatelinenum = "$enddatelinenum


echo -e "Finding the range of the data."
reg=$(gmt info -h1 -Vl -I0.000001 -i$lonlinenum,$latlinenum $InSARdata)
echo "Range is given as "$reg

echo -e "Gridding both dates"
gmt xyz2grd -Gfirstdate.tmp.nc -I$pixelsize $reg $InSARdata -i$lonlinenum,$latlinenum,$startdatelinenum -Dlon/lat -h1
gmt xyz2grd -Genddate.tmp.nc -I$pixelsize $reg $InSARdata -i$lonlinenum,$latlinenum,$enddatelinenum -Dlon/lat -h1

echo -e "Differencing the two grids"
gmt grdmath enddate.tmp.nc firstdate.tmp.nc SUB = difference.tmp.nc
gmt grd2xyz difference.tmp.nc -s > plotting.tmp

echo -e "Making colourscale; it will automatically be symmetric about zero."
#gmt grd2cpt difference.tmp.nc -Cred2green -T= -Z > colours.cpt.tmp
gmt makecpt -Cred2green -T-350/350 -V > colours.cpt.tmp # makes colours for InSAR. THIS CAN BE MADE

echo -e "\tForming the map."
gmt psbasemap $reg $proj --MAP_FRAME_TYPE=inside -BSWne -Bxya -K > $outputname.ps # Plot the map frame.
gmt grdimage difference.tmp.nc $proj -Ccolours.cpt.tmp -Q -O -K >> $outputname.ps
#gmt grdimage grid_interp.tmp.nc $proj -Ccolours.cpt.tmp -Q -O -K >> $outputname.ps

echo -e "\tPutting contours on top."
gmt triangulate -Ggrid_interp.tmp.nc -I$pixelsize $reg plotting.tmp -Vl
gmt grdcontour $proj grid_interp.tmp.nc -A$contour_int+f11p -Q40k -W2.5p -O -V >> $outputname.ps
gmt psconvert $outputname.ps -TG -E720 -W+k+t$toplotfilename+l256/-1
gmt psconvert $outputname.ps -TG -E720 -W+g


# Do a separate scalebar
echo "Making a separate colourbar with name colorbar.png. Will overwrite an existing file with that time."
gmt psscale -Ccolours.cpt.tmp -Dx8c/1c+w12c/0.5c+jTC+h -Bxaf+l"Deformation / mm" -P > $outputname.colorbar.ps
gmt psconvert $outputname.colorbar.ps -Tg -A

if [ "$debugflag" = "y" ]; then 
	echo "debugflag is set to '$debugflag'; not deleting temp files"; 
else 
	echo "debugflag is unset; removing temporary files"
	rm *tmp*;
	rm *.ps; 	
fi

open $outputname.png

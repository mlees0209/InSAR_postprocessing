#!/bin/bash

### This script plots the final timestep of a big InSAR file. The result is a kml and a png. The scalebar is also outputted separately. If DEBUGFLAG is y, then temporary .tmp and .ps files are retained. Contours should be y or n, if y you will get a contour map as well (which takes ages to form and is likely dodgy...at this stage.). I have edited this file a bit to work for a specific dataset.

if [ "$#" -lt 3 ]; then
    echo "Useage: ./plot_final_timestep InSARdata pixelsize outputname contours [debugflag]"
    exit 2
fi


InSARdata=$1
pixelsize=$2
outputname=$3
contours=$4
debugflag=$5

myInvocation="$(printf %q "$BASH_SOURCE")$((($#)) && printf ' %q' "$@")"
echo "Command called was "$myInvocation" which is written in "$outputname".info."
echo -e "Command called was:" > $outputname.info
echo "$myInvocation" >> $outputname.info

proj="-JX15ig" # the final 'g' tells GMT  that this is a linear, geographic projection
#proj='-JM5i'
gmt set PS_MEDIA A2
gmt set FONT_ANNOT_PRIMARY 16p
gmt set FONT_LABEL 20p

echo -e "\tFinding the last column of the InSARdata, and finding which column is lat/lon."

if grep -q "Latitude" $InSARdata ; then
	echo 'things are going fine'
	latlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "Latitude" | tr -d ':Latitude')
	latlinenum=$(( $latlinenum - 1 ))
	echo "Latlinnum = "$latlinenum
	lonlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "Longitude" | tr -d ':Longitude')
	lonlinenum=$(( $lonlinenum - 1 ))
	echo "Lonlinenum = "$lonlinenum
	elif grep -q "X" $InSARdata ; then
		latlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "Y" | tr -d ':Y')
		latlinenum=$(( $latlinenum - 1 ))
		echo "Latlinnum = "$latlinenum
		lonlinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n "X" | tr -d ':X')
		lonlinenum=$(( $lonlinenum - 1 ))
		echo "Lonlinenum = "$lonlinenum
	else echo $InSARdata' does not have column Latitude or X. Aborting!'
	exit 2; 
fi


finaldate=$(head -1 $InSARdata | rev | cut -d',' -f1 | rev)
maxdeflinenum=$(head -1 $InSARdata | tr ',' '\n' | grep -n $finaldate | cut -d ':' -f1)
maxdeflinenum=$(( $maxdeflinenum - 1 ))
echo "Finallinenum = "$maxdeflinenum

echo -e "Finding the range of the data."
reg=$(gmt info -h1 -Vl -I0.000001 -i$lonlinenum,$latlinenum $InSARdata)
echo "Range is given as "$reg

echo "Making the plotting file plotting.tmp"
nodataentries=$(gmt info $InSARdata -Fi | cut -f5)

yes $pixelsize | head -n $nodataentries > pixelsize.tmp

gmt convert -o$lonlinenum,$latlinenum,$maxdeflinenum -h1 $InSARdata > plotting.tmp

yes "0" | head -n $nodataentries > azimuth.tmp

paste plotting.tmp azimuth.tmp > plotting3.tmp
paste plotting3.tmp pixelsize.tmp > plotting2.tmp
paste plotting2.tmp pixelsize.tmp > plotting.tmp

maxdef=$(gmt info -T1+c2 plotting.tmp | cut -d '/' -f 2) # This command assumes that the maximum deformation is in the positive direction.
echo "maxdef is "$maxdef

echo -e "\tForming a coloured-point map."

gmt psbasemap $reg $proj --MAP_FRAME_TYPE=inside -BSWne -Bxya -K > $outputname.ps # Plot the map frame.

gmt makecpt -Cred2green -T-650/650 -V > colours.cpt.tmp # makes colours for InSAR. THIS CAN BE MADE AUTOMATIC, get colours from the InSAR data and force symmetric, but I haven't done that yet.
gmt psxy $reg $proj plotting.tmp -Ccolours.cpt.tmp -SJ -V -O >> $outputname.ps

if [ "$contours" = "y" ]; then
	echo -e "\tForming a contour map."
	gmt psbasemap $reg $proj --MAP_FRAME_TYPE=inside -BSWne -Bxya -K > $outputname-contour.ps 
	gmt makecpt -Cred2green -T-800/0/80 > colours.contours.tmp.cpt
	gmt pscontour $reg $proj plotting.tmp -Ccolours.contours.tmp.cpt -I -W2.5p -Q10 -Vl -O >> $outputname-contour.ps
	# Convert the contours too
	gmt psconvert $outputname-contour.ps -TG -E720 -W+k
	gmt psconvert $outputname-contour.ps -TG -E720 -W+g
else echo 'Contour set to '$contour" so not producing a contour map.";
fi

gmt psconvert $outputname.ps -TG -E720 -W+k+t$toplotfilename+l256/-1
gmt psconvert $outputname.ps -TG -E720 -W+g


# Do a separate scalebar
echo "Making a separate colourbar with name colorbar.png. Will overwrite an existing file with that time."
gmt psscale -Ccolours.cpt.tmp -Dx8c/1c+w12c/0.5c+jTC+h -Bxaf+l"Deformation / mm" -P > $outputname.colorbar.ps
gmt psconvert $outputname.colorbar.ps -Tg -A

if [ -z "$debugflag" ]; then 
	echo "debugflag is unset; removing temporary files"
	rm *tmp*;
	rm *.ps; 	
else 
	echo "debugflag is set to '$debugflag'; not deleting temp files"; 
fi


open $outputname.png

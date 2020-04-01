# This script will plot a pdf and create a kmz showing the footprints of L0 Sentinel Data downloaded into a given directory. The kml is better as the pdf map hasn't been set up to change the range to match the footprints.
#
# Usage: check_footprints_L0.sh DIRECTORY <--- where DIRECTORY is the directory containing the unzipped .SAFE directories containing L0 data.

# Set up variables
echo -e "WARNING; this script will delete any kml (but not kmz) files in the current directory. Run it in an empty directory if this will be a problem!"
echo -e

# Create an info file
myInvocation="$(printf %q "$BASH_SOURCE")$((($#)) && printf ' %q' "$@")"
echo "Command called was "$myInvocation" which is written in "footprints".info."
echo -e "Command called was:" > footprints.info
echo "$myInvocation" >> footprints.info


folder=$1
source gmt_shell_functions.sh

echo -e "Getting L0 footprints from "$folder
ls -d $folder/*.SAFE > filenames.tmp # get the list of .SAFE files
touch out.tmp
touch orbitnames.tmp
nofootprints=$(wc -l < filenames.tmp | tr -d '[:space:]')
echo -e "Number of footprints (frames) found = "$nofootprints

gmt makecpt -Crainbow -A40 -T0/$nofootprints/1 > colors.cpt.tmp # made the colours for the footprint polygons.

echo Making Footprints....
no=1
cat filenames.tmp | while read line
do
no=$(($no + 1))
orbitnum=$(grep 'relativeOrbitNumber type="start"' $line/manifest.safe | grep -o '>.*<' | tr -d '<' | tr -d '>')
cyclenum=$(grep 'cycleNumber' $line/manifest.safe | grep -o '>.*<' | tr -d '<' | tr -d '>')
echo "	Getting footprint for Orbit number "$orbitnum", cycle number "$cyclenum
orbitname="O${orbitnum}_C${cyclenum}"
echo $orbitname >> orbitnames.tmp
col=$(cut -f2 colors.cpt.tmp | sed -n $no'p') # get the colour code from the .cpt file previously made.
# Make the table for the pdf
echo -e "> -G$col" >> out.tmp
grep -A1 'footPrint' $line/manifest.safe | sed -n 2p | grep -o '>.*<' | tr -d '<' | tr -d '>' | tr " " "\n" >> out.tmp # Get the coordinates from the .manifest file
# Make the file for the kml
grep -A1 'footPrint' $line/manifest.safe | sed -n 2p | grep -o '>.*<' | tr -d '<' | tr -d '>' | tr " " "\n" | tr "," " " > kmlmaker.tmp
linefilename=$(echo $line | rev | cut -d"/" -f1 | rev)
echo -e "	"$linefilename
gmt 2kml kmlmaker.tmp -Fp -Gf$col -:i > $linefilename.kml
done

gmt_build_kmz -p "footprints" *SAFE.kml # Stich together all the individual footprint km into one kmz
lastkmlfilename=`tail -n 1 filenames.tmp| cut -d / -f 2`

mv $lastkmlfilename.kmz footprints.kmz

### OPTIONAL SECTION: make a pdf map. Can comment this out.

# #!# Set variables - edit with relatively little fear of breaking everything... #!#
# proj="-JM8i" # Mercator projection
# proj="-JB-120/0/34/40.5/5i" # this is an Albers projection if you ever want (but you probably don't).
# outputname="footprint_map" 
# reg="-R-121/-117/34/37.75" # plotting region.
# 
# Set global parameters
# gmt set PS_MEDIA A2
# gmt set MAP_GRID_PEN_PRIMARY 0.3p,black,-
# gmt set FONT_LABEL 10p
# gmt set FONT_ANNOT_PRIMARY 10p
# 
# #!# Main code - edit with plenty of fear that everything might break! #!#
# 
# # Basemap things
# echo -e "Making basemap"
# gmt grdimage ~/Box/bigdata/Google_Satellite_Imagery/SouthCentralValley_zoom11.tif $proj -D -t2 $reg -K > $outputname.ps # plot background satellite image, can change zoom here if u want.
# gmt psbasemap $reg $proj -BNWse -Bxy1 -LjBL+c36+w100k+f+u+o1/0.75 -Fl+gwhite@50 -O -K >> $outputname.ps # Basemap: includes gridlines, map border, scale bar.
# echo "Footprint_map" | gmt pstext $reg $proj -F+cTL+f12,Helvetica-Bold,black -Gwhite@50 -D0.2/-0.2 -P -O -K >> $outputname.ps # Write a little title.
# 
# 
# # Basin plotting and things
# echo -e "Plotting the footprints"
# gmt makecpt -Crainbow -A50 -T0/25/1 > colors.cpt.tmp
# gmt psxy $reg $proj out.tmp -Ccolors.cpt.tmp -:i -W0.3p+c -O -K >> $outputname.ps # plot the basin polygons. These polygons were previously created using a gmt kml2gmt line which got lost somewhere...
# 
# no=0
# while read NO; 
# do
# 	no=$((no + 1))
# 	a='G 0.05i'
# 	d='S L s 0.15i z='$no' 0.25p 0.3i '
# 	b=$NO
# 	c=$d$b
# 	echo $c >> TEST.tmp
# 	echo -e $a >> TEST.tmp
# done<orbitnames.tmp
# 
# echo -e "A colors.cpt.tmp" | cat - TEST.tmp > legend.tmp
#  
# Plot the legend
# gmt pslegend $reg $proj -F+c-0.1+gwhite@15+pblack -DJTR+w1.5i+jTR -C0.2/0.2 -O < legend.tmp >> $outputname.ps

### Tidy up and convert to pdf.
echo -e "Tidying up..."

#gmt psconvert $outputname.ps -A -P -Tf
#rm $outputname.ps
rm *tmp*
#open $outputname.pdf

#!/bin/sh

OUTPUTDIR="/tmp/feyn"
OUTPUTDIR="/var/www/feyn/straight"

for i in `ls ../../lhe/*.lhe`; do
	j=`echo $i | sed -e 's;.*lhe/;;' | sed -e 's/_.\.lhe$//'`;
	echo $j;
	./feynmanGraph.py -T $j -s -i -o $OUTPUTDIR/${j}_feyn.pdf
	convert $OUTPUTDIR/${j}_feyn.pdf $OUTPUTDIR/${j}_feyn.png
done

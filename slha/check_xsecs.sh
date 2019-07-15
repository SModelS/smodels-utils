#!/bin/sh

## super simple script that produces xsecs for slha files, 
## in case there arent any

for i in `ls T6WW*slha | shuf`; do
	H=`cat $i | grep -i xsection | wc -l`
	[ "$H" -eq "0" ] && { echo "[check_xsecs.sh] no xsecs found in $i"; ~/git/smodels/smodelsTools.py xseccomputer -f $i -8 -P -N -e 50000; }
done

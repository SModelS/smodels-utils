#!/bin/sh

## super simple script that produces xsecs for slha files, 
## in case there arent any

for i in `ls T*slha | tail -n 500`; do
	H=`cat $i | grep -i xsection | wc -l`
#	echo "$i $H"
	[ "$H" -eq "0" ] && { echo "[check_xsecs.sh] no xsecs found in $i"; ~/git/smodels/smodelsTools.py xseccomputer -f $i -8 -P -N -e 10000; }
done

#!/bin/sh

## super simple script that produces xsecs for slha files, 
## in case there arent any

T="T6WW*slha"

[ "x$1" != "x" ] && T=$1;

echo "check $T";

for i in `ls $T | shuf`; do
	H=`cat $i | grep -i xsection | wc -l`
	[ "$H" -eq "0" ] && { echo "[check_xsecs.sh] no xsecs found in $i"; ~/git/smodels/smodelsTools.py xseccomputer -f $i -8 -P -N -c 10 -e 50000; }
done

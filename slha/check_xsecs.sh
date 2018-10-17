#!/bin/sh

## super simple script that produces xsecs for slha files, 
## in case there arent any

for i in `ls T*slha`; do
	H=`cat $i | grep -i xsection | wc -l`
	[ "$H" -eq "0" ] && { echo "$i, $H"; ~/git/smodels/smodelsTools.py xseccomputer -f $i -8 -P -N; }
done

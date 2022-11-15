#!/bin/sh

## super simple script that produces xsecs for slha files, 
## in case there arent any

TOTAL=`ls T*slha | wc -l`
ZEROES=0

for i in `ls T*slha`; do
	H=`cat $i | grep -i xsection | wc -l`
	[ "$H" -eq "0" ] && ZEROES=$(($ZEROES + 1))
done

echo $ZEROES / $TOTAL have no xsecs. | tee log

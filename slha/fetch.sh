#!/bin/sh

## script that fetches all tarballs from server

URL="http://smodels.hephy.at/downloads/tarballs"

rm -f ls *.tar
wget $URL/ls

for i in `cat ls`; do
	echo $i; wget $URL/$i;
done

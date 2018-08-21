#!/bin/sh

for i in `ls -d CMS* | grep -v .png | grep -v .txt | grep -v .pcl`; do
	echo "cding into $i";
	cd $i; ./fetch.py; cd ..
done

#!/bin/sh

DB=../../smodels-database

for i in `ls -d $DB/*TeV/*/`; do
	echo ">>$i<<"
	for j in `ls -d ${i}*/validation/`; do
		echo ">>>$j<<<"
		cp scripts/*.py $j/
	done
done

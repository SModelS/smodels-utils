#!/bin/sh

cd /mnt/hephy/pheno/ww/git/smodels-utils/EM_Creator
./bake.py -p 10 -t T6WW -b --copy -n 50000 -a --maxgap2 80. -m "[(300,1099,25),'half',(200,999,25)]"

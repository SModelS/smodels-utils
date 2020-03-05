#!/bin/sh

cd /mnt/hephy/pheno/ww/git/smodels-utils/EM_Creator
./bake.py -p 30 -t T3GQ --analyses cms_sus_16_033 -n 10000 -a -m "[(50,4600,100),(50,4600,100),(0.)]"

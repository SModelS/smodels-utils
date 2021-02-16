#!/bin/sh

cd /mnt/hephy/pheno/ww/git/smodels-utils/validation

echo "starting slha creator for thscpm7 .... "
./slhaCreator.py -t THSCPM7 -a "[[x, x-100, (y, z)], [x, (y, z)]]" --xmin 900. --xmax 2500. --dx 100. --ymin 325. --ymax 2400. --dy 100. --zmin 1e-16 --zmax 2e-16 --dz 10. -lz -n 5000 -8 -p 5 --no_xsecs

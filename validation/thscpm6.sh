#!/bin/sh

cd /mnt/hephy/pheno/ww/git/smodels-utils/validation

./slhaCreator.py -t THSCPM6 -a "[[x, x, (y, z)], [x, x, (y, z)]]" --xmin 900. --xmax 2500. --dx 50. --ymin 25. --dy 2100. --dy 50. --zmin 1e-17 --zmax 2e-15 --dz 10. -lz  -n 10000 -8 -p 70

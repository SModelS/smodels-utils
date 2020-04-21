#!/bin/sh

cd /mnt/hephy/pheno/ww/git/smodels-utils/validation

# ./slhaCreator.py -t THSCPM5 -a "[[x, x, (y, z)], [x, x, (y, z)]]" --xmin 900. --xmax 2500. --dx 100. --ymin 25. --dy 2100. --dy 100. --zmin 1e-17 --zmax 2e-15 --dz 10. -lz  -n 5000 -8 -p 5 

echo "starting slha creator for thscpm4 at `hostname`"
echo "working dir: `pwd`"
echo "python3: `which python3`"
./slhaCreator.py -t THSCPM4 -a "[[x, (y, 1e-16)], [x, (y, 1e-16)]]" --xmin 50. --xmax 3010. --dx 100. --ymin 40. --ymax 2920. --dy 100. -n 5000 -8 -p 10 --no_xsecs
echo "done slha creator"

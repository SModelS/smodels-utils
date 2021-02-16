#!/bin/sh

cd /mnt/hephy/pheno/ww/git/smodels-utils/validation

# ./slhaCreator.py -t THSCPM5 -a "[[x, x, (y, z)], [x, x, (y, z)]]" --xmin 900. --xmax 2500. --dx 100. --ymin 25. --dy 2100. --dy 100. --zmin 1e-17 --zmax 2e-15 --dz 10. -lz  -n 5000 -8 -p 5 

echo "starting slha creator for thscpm2b at `hostname`"
echo "working dir: `pwd`"
echo "python3: `which python3`"
./slhaCreator.py -t THSCPM2b -a "[[(x, y)], [(x, y)]]" --xmin 40. --xmax 3510. --dx 100. --ymin 1e-22 --ymax 2e-15 --dy 10. -ly -n 20000 -8 -p 10 --no_xsecs
echo "done slha creator"

#!/bin/sh

#cd /mnt/hephy/pheno/ww/git/smodels-utils/validation/

echo "Running validation on `hostname`"
python runValidation.py -p validation_parameters.ini -v debug
# ./slhaCreator.py -t THSCPM8 -a "2*[[x,(y,z)]]" --xmin 300. --xmax 2800. --dx 100. --ymin 280. --ymax 2000. --dy 100. -p 70 -8 -n 5000 --zmin 1e-17 --zmax 2e-15 --dz 10.  -lz

#!/bin/bash

source /mnt/hephy/pheno/opt/root/bin/thisroot.sh
cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation
./runValidation.py -p @@INIFILE@@
sleep 5
rm $0

#!/bin/bash

SCRIPT=$(readlink -f $0)

source /groups/hephy/pheno/opt/root/bin/thisroot.sh
cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation
./runValidation.py -p @@INIFILE@@
sleep 5
rm $SCRIPT

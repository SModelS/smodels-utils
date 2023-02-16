#!/bin/bash

SCRIPT=$(readlink -f $0)

ml unload gcc
ml unload anaconda3
ml unload build-env

export PYTHONPATH="/scratch-cbe/users/wolfgan.waltenberger/git/smodels:/scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils"
source /groups/hephy/pheno/opt/root/bin/thisroot.sh

cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation
./runValidation.py -p @@INIFILE@@
sleep 5
rm @@INIFILE@@
rm $SCRIPT

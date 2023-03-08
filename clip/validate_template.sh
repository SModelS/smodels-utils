#!/bin/bash

SCRIPT=$(readlink -f $0)

cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation
./runValidation.py -p @@INIFILE@@
sleep 5
rm @@INIFILE@@
# rm $SCRIPT

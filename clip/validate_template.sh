#!/bin/bash

SCRIPT=$(readlink -f $0)

ml load texlive/20210324-gcccore-10.2.0

cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation
./runValidation.py -p @@INIFILE@@
sleep 5
rm @@INIFILE@@
# rm $SCRIPT

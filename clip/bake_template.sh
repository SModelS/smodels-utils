#!/bin/bash

SCRIPT=$(readlink -f $0)

source /groups/hephy/pheno/opt/root/bin/thisroot.sh
cd /scratch-cbe/users/wolfgan.waltenberger/git/em-creator
./bake.py @@ARGS@@
sleep 5
rm $SCRIPT

#!/bin/bash

SCRIPT=$(readlink -f $0)

@@SOURCE_ENV@@

# source /groups/hephy/pheno/opt/root/bin/thisroot.sh
cd /scratch-cbe/users/wolfgan.waltenberger/git/em-creator
test -e ./rmOld.py && ./rmOld.py # clean out regularly
./bake.py @@ARGS@@
sleep 5
rm $SCRIPT

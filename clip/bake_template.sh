#!/bin/sh

# cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/EM_Creator
cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/EM_Creator
./bake.py @@ARGS@@
sleep 5
rm $0

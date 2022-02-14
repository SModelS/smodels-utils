#!/bin/sh

SCRIPT=$(readlink -f $0)

## ml --latest singularity
# cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip/temp/@@SCRIPT@@ -H /scratch-cbe/users/wolfgan.waltenberger/git/em-creator /scratch-cbe/users/wolfgan.waltenberger/container/current.simg

sleep 5
rm $SCRIPT

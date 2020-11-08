#!/bin/sh

## ml --latest singularity

cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip/@@SCRIPT@@ -H /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/EM_Creator /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
#singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip/@@SCRIPT@@ -H /mnt/hephy/pheno/ww/git/smodels-utils/EM_Creator /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
sleep 5
rm $0

#!/bin/sh

## ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip/@@SCRIPT@@ -H /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
#singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip/@@SCRIPT@@ -H /groups/hephy/pheno/ww/git/em-creator /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
sleep 5
rm $0

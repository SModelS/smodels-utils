#!/bin/sh

ml --latest singularity

cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s /mnt/hephy/pheno/ww/git/smodels-utils/clip/@@SCRIPT@@ -H /mnt/hephy/pheno/ww/git/smodels-utils/EM_Creator /mnt/hephy/pheno/current.simg

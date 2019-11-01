#!/bin/sh

ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/
cd /mnt/hephy/pheno/ww/git/smodels-utils/validation

singularity shell -c -B /tmp,/run,/scratch -s /mnt/hephy/pheno/ww/git/smodels-utils/validation/thscpm8.sh -H /mnt/hephy/pheno/ww/ /mnt/hephy/pheno/ubuntu1904sing34.simg


#!/bin/sh

### ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/
cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation

singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/validation/thscpm8.sh -H /groups/hephy/pheno/ww/ /scratch-cbe/users/wolfgan.waltenberger/container/current.simg


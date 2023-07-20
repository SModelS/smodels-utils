#!/bin/sh

SCRIPT=$(readlink -f $0)

## ml --latest singularity
# cd /users/wolfgan.waltenberger/git/projects/singularity/

#ml unload gcc/10.2.0
#ml unload anaconda3/2021.11
#ml unload build-env/f2021

ml unload gcc
ml unload anaconda3
ml unload build-env

export PYTHONPATH="/scratch-cbe/users/wolfgan.waltenberger/git/smodels"
export PATH=.:/-scratch-cbe/users/wolfgan.waltenberger/.local/bin:$PATH

singularity shell -c -B /tmp,/run,/scratch -s /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip/temp/@@SCRIPT@@ -H /scratch-cbe/users/wolfgan.waltenberger/git/em-creator /scratch-cbe/users/wolfgan.waltenberger/container/current.simg

sleep 5
rm $SCRIPT

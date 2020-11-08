#!/bin/sh

## ml --latest singularity

cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/clip

singularity shell -c -B /tmp,/run,/scratch -s walkingWorker.py -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg

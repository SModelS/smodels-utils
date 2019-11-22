#!/bin/sh
###SBATCH --ntasks-per-node=40.

ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

## --nv for cuda
singularity shell -c -B /tmp,/run,/scratch -s /mnt/hephy/pheno/ww/git/smodels-utils/combinations/walkingWorker.py -H /mnt/hephy/pheno/ww /mnt/hephy/pheno/current.simg


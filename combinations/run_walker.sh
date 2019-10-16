#!/bin/sh

ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

## --nv for cuda
singularity shell -c -B /tmp,/run,/scratch -s /mnt/hephy/pheno/ww/git/smodels-utils/combinations/walkingWorker.py -H /mnt/hephy/pheno/ww /mnt/hephy/pheno/ubuntu1904sing34.simg

###SBATCH --ntasks-per-node=20.

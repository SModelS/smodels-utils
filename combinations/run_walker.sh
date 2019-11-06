#!/bin/sh

ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

## --nv for cuda
singularity shell -c -B /tmp,/run,/scratch -s walkingWorker.py -H /mnt/hephy/pheno/ww /mnt/hephy/pheno/current.simg

###SBATCH --ntasks-per-node=20.

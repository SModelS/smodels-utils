#!/bin/sh

ml --latest singularity

cd /users/wolfgan.waltenberger/git/projects/singularity/

## --nv for cuda
singularity shell -c -B /tmp,/run,/scratch -s /users/wolfgan.waltenberger/walkingWorker.py -H /users/wolfgan.waltenberger ./schroedinger.simg

###SBATCH --ntasks-per-node=20.

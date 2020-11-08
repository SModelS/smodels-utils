#!/bin/sh

# super simple script that runs the hiscore and state updater on a worker.
# in between updates it waits 10 mins

## ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s @@RUNDIR@@/upHi.py -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg

###SBATCH --ntasks-per-node=20.

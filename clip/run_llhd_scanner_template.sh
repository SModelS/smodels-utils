#!/bin/sh

# super simple script that runs the hiscore and state updater on a worker.
# in between updates it waits 10 mins

## ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /scratch-cbe/users/wolfgan.waltenberger/tmp:/tmp,/run,/scratch -s @@RUNDIR@@/llhdscanner@@PID@@.sh -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg ## version with temp dir moved
# singularity shell -c -B /tmp:/tmp,/run,/scratch -s @@RUNDIR@@/llhdscanner@@PID@@.sh -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg

###SBATCH --ntasks-per-node=20.

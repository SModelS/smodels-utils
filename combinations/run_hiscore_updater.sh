#!/bin/sh

# super simple script that runs the hiscore and state updater on a worker.
# in between updates it waits 10 mins

ml --latest singularity

cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s /users/wolfgan.waltenberger/updateHiscores.py -H /users/wolfgan.waltenberger ./ubuntu1904sing34.simg

###SBATCH --ntasks-per-node=20.

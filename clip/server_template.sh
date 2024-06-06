#!/bin/sh

# super simple script that runs the hiscore and state updater on a worker.
# in between updates it waits 10 mins

## ml --latest singularity

# cd /users/$USER/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s @@RUNDIR@@/run_proxy.sh -H @@RUNDIR@@ /scratch-cbe/users/$USER/container/current.simg

###SBATCH --ntasks-per-node=20.

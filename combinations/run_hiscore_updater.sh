#!/bin/sh

# super simple script that runs the hiscore and state updater on a worker.
# in between updates it waits 10 mins

ml --latest singularity

# cd /users/wolfgan.waltenberger/git/projects/singularity/

singularity shell -c -B /tmp,/run,/scratch -s /mnt/hephy/pheno/ww/git/smodels-utils/combinations/updateHiscores.py -H /mnt/hephy/pheno/ww/ /mnt/hephy/pheno/ubuntu1904sing34.simg

###SBATCH --ntasks-per-node=20.

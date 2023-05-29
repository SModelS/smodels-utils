#!/bin/sh
# ml --latest singularity
#ml singularity/3.1.0

# cd /users/wolfgan.waltenberger/git/projects/singularity/

unset HOSTFILE
unset LD_LIBRARY_PATH

/users/wolfgan.waltenberger/copyEnv.py

ml unload gcc/12.2.0 > /dev/null 2>&1
ml unload anaconda3/2022.05 > /dev/null 2>&1
ml unload build-env/f2022 > /dev/null 2>&1
ml unload gcc/12.2.0 > /dev/null 2>&1

singularity shell --env-file /users/wolfgan.waltenberger/.containerrc -c -B /groups/hephy,/scratch-cbe/users/wolfgan.waltenberger:/local/wwaltenberger,/scratch-cbe/users/wolfgan.waltenberger:/home/walten,/scratch-cbe/users/wolfgan.waltenberger/tmp:/tmp,/run,/scratch -s /bin/bash -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
# singularity shell --env 'PS1="[sing] \[\e[32;11m\]\h \[\e[0;33;11m\]\w> \[\033k\033\134\033 \e[37;0m\]"' -c -B /groups/hephy,/scratch-cbe/users/wolfgan.waltenberger:/local/wwaltenberger,/scratch-cbe/users/wolfgan.waltenberger:/home/walten,/scratch-cbe/users/wolfgan.waltenberger/tmp:/tmp,/run,/scratch -s /bin/bash -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg

ml load build-env/f2022 > /dev/null 2>&1
ml load gcc/12.2.0 > /dev/null 2>&1
ml load anaconda3/2022.05 > /dev/null 2>&1
ml load gcc/12.2.0 > /dev/null 2>&1

#!/bin/sh
# ml --latest singularity
#ml singularity/3.1.0

# cd /users/$USER/git/projects/singularity/

unset HOSTFILE
unset LD_LIBRARY_PATH

/users/$USER/copyEnv.py

ml unload gcc/12.2.0 > /dev/null 2>&1
ml unload anaconda3/2023.03 > /dev/null 2>&1
ml unload build-env/f2022 > /dev/null 2>&1

ml unload gcc/10.2.0
ml unload build-env/f2021
ml unload anaconda3/2021.11

singularity shell --cleanenv --env-file /users/$USER/.containerrc -c -B /groups/hephy,/scratch-cbe/users/$USER:/local/wwaltenberger,/scratch-cbe/users/$USER:/home/walten,/scratch-cbe/users/$USER/tmp:/tmp,/run,/scratch -s /bin/bash -H /scratch-cbe/users/$USER /scratch-cbe/users/$USER/container/current.simg
# singularity shell --env 'PS1="[sing] \[\e[32;11m\]\h \[\e[0;33;11m\]\w> \[\033k\033\134\033 \e[37;0m\]"' -c -B /groups/hephy,/scratch-cbe/users/$USER:/local/wwaltenberger,/scratch-cbe/users/$USER:/home/walten,/scratch-cbe/users/$USER/tmp:/tmp,/run,/scratch -s /bin/bash -H /scratch-cbe/users/$USER /scratch-cbe/users/$USER/container/current.simg
type -t ml 1>/dev/null && ml -q load build-env/f2022
type -t ml 1>/dev/null && ml load anaconda3/2023.03
type -t ml 1>/dev/null && ml load nodejs/18.12.1-gcccore-12.2.0
type -t ml 1>/dev/null && ml load gcc/12.2.0 
type -t ml 1>/dev/null && ml load texlive/20220321-gcc-12.2.0

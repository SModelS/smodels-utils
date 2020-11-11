#!/bin/sh
# ml --latest singularity
#ml singularity/3.1.0

# cd /users/wolfgan.waltenberger/git/projects/singularity/

unset HOSTFILE

singularity shell --env 'PS1=[sing] \[\e[32;11m\]\h \[\e[0;33;11m\]\w> \[\033k\033\134\033 \e[37;0m\]' -c -B /scratch-cbe/users/wolfgan.waltenberger:/local/wwaltenberger,/scratch-cbe/users/wolfgan.waltenberger:/home/walten,/scratch-cbe/users/wolfgan.waltenberger/tmp:/tmp,/run,/scratch -s /bin/bash -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
#singularity shell --env 'PS1=[sing] \e[32;11m\]\h \e[0;33;11m\]\w> \[\033k\033\134\033 \e[37;0m\]' -c -B /scratch-cbe/users/wolfgan.waltenberger:/local/wwaltenberger,/scratch-cbe/users/wolfgan.waltenberger:/home/walten,/scratch-cbe/users/wolfgan.waltenberger/tmp:/tmp,/run,/scratch -s /bin/bash -H /scratch-cbe/users/wolfgan.waltenberger /scratch-cbe/users/wolfgan.waltenberger/container/current.simg
# singularity shell -c -B /scratch-cbe/users/ww:/local/wwaltenberger,/mnt/hephy/pheno/ww:/home/walten,/tmp,/run,/scratch -s /bin/bash -H /mnt/hephy/pheno/ww /mnt/hephy/pheno/current.simg

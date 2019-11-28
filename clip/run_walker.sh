#!/bin/sh

ml --latest singularity

cd /mnt/hephy/pheno/ww/git/smodels-utils/clip

singularity shell -c -B /tmp,/run,/scratch -s /mnt/hephy/pheno/ww/git/smodels-utils/clip/walkingWorker.py -H /mnt/hephy/pheno/ww /mnt/hephy/pheno/current.simg

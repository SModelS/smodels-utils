#!/bin/sh

#cd /scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/EM_Creator
cd /scratch-cbe/users/wolfgan.waltenberger/git/em-creator
./bake.py -p 10 -t TGQ -n 10000 -a --analyses "cms_sus_16_033,atlas_susy_2016_07" -m "[(50,4500,200),(50,4500,200),(0.)]"

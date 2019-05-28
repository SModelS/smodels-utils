#!/bin/sh

scp gpu:/local/wwaltenberger/git/smodels-utils/combinations/hiscore.pcl .
./checkHiscores.py -f hiscore.pcl -t 1 -s best.pcl

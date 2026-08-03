#!/bin/sh

rm -rf /tmp/full_*
[ -e "full_slep" ] && mv full_slep /tmp
[ -e "full_chiwzoff" ] && mv full_chiwzoff /tmp
mkdir -p full_slep
mkdir -p full_chiwzoff
scp -r clip-login-1:git/smodels-utils/stats_ml/full_slep/\*.csv full_slep
scp -r clip-login-1:git/smodels-utils/stats_ml/full_slep/\*.json full_slep
scp -r clip-login-1:git/smodels-utils/stats_ml/full_chiwzoff/\*.csv full_chiwzoff
scp -r clip-login-1:git/smodels-utils/stats_ml/full_chiwzoff/\*.json full_chiwzoff
#rm -rf full_*/*.temp

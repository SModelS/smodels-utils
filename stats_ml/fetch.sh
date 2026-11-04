#!/bin/sh

#rm -rf /tmp/full_*
#[ -e "full_slep" ] && mv full_slep /tmp
#[ -e "full_chiwzoff" ] && mv full_chiwzoff /tmp
#mkdir -p full_slep
#mkdir -p full_chiwzoff
scp -r cbe.next:git/smodels-utils/stats_ml/19\*.csv .

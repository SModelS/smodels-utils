#!/bin/sh
unset PYTHONPATH

ml load anaconda3/2022.05
PYTHONPATH=/users/wolfgan.waltenberger/git/smodels:/users/wolfgan.waltenberger/git/smodels-utils:/users/wolfgan.waltenberger/.local/lib/python3.9/site-packages:/software/f2022/software/python/3.9.6-gcccore-11.2.0/lib/python3.9/site-packages:/users/wolfgan.waltenberger/git/protomodels:$PYTHONPATH
PYTHONPATH=$(echo -n $PYTHONPATH | awk -v RS=: -v ORS=: '!x[$0]++' | sed "s/\(.*\).\{1\}/\1/")

#!/bin/sh

WORKER=" --time=239 --mem-per-cpu=4GB --reservation interactive -c 10 "
# WORKER=" --time=479 --mem-per-cpu=4GB --reservation interactive -c 10 -c 'source ~/my_env; exec bash -i' "
# WORKER=" -c 30 " # --time 45:00 "
[ "x$1" != "x" ] && WORKER=" -w $1 ";

echo "srun $WORKER --pty bash "
srun $WORKER --pty bash

#!/bin/sh

# WORKER=" --time=479 --mem-per-cpu=10GB --reservation interactive -c 10 "
# WORKER=" --time=2879 --reservation interactive -c 30 "
WORKER=" --time=479 --mem-per-cpu=6GB --reservation interactive -c 20 "
# WORKER=" -c 30 " # --time 45:00 "
[ "x$1" != "x" ] && WORKER=" -w $1 ";

echo "srun $WORKER --pty bash"
srun $WORKER --pty bash

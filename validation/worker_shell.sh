#!/bin/sh

WORKER=" --cores-per-socket=10 --cpus-per-task=10 -n 10 "
[ "x$1" != "x" ] && WORKER=" -w $1 ";

echo "srun $WORKER --pty bash"
srun $WORKER --pty bash

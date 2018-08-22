#!/bin/sh

rm -rf smodels.simg
sudo singularity build --writable smodels.simg Singularity.smodels

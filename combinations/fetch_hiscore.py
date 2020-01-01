#!/usr/bin/env python3

import subprocess, sys

f="hiscore.pcl"
if len(sys.argv)>1 and "s" in sys.argv[1]:
	f="s\*.pcl"
cmd="scp wolfgan.waltenberger@clip-login-1:/mnt/hephy/pheno/ww/rundir/%s ." % f
print ( cmd )
out = subprocess.getoutput ( cmd )
print ( out )

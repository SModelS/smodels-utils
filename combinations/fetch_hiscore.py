#!/usr/bin/env python3

import subprocess, sys

f= [ "hiscore.pcl" ]
if len(sys.argv)>1 and "scan" in sys.argv[1]:
	f= [ "scanM\*.pcl", "mp\*.pcl", "ssm\*.pcl" ]
if len(sys.argv)>1 and "copy" in sys.argv[1]:
	f= [ "hiscoreCopy.pcl" ]
if len(sys.argv)>1 and "ssm" in sys.argv[1]:
	f= [ "ssm\*.pcl" ]
for i in f:
    cmd="scp wolfgan.waltenberger@clip-login-1:/mnt/hephy/pheno/ww/rundir/%s ." % i
    print ( cmd )
    out = subprocess.getoutput ( cmd )
    print ( out )

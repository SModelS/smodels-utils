#!/usr/bin/env python3

import subprocess, sys, copy

f= [ "hiscore.pcl" ]
if len(sys.argv)>1:
    oldf = copy.deepcopy(f)
    if "scan" in sys.argv[1]:
	    f= [ "scanM\*.pcl", "mp\*.pcl", "ssm\*.pcl" ]
    if "states" in sys.argv[1]:
	    f= [ "states.pcl" ]
    if "copy" in sys.argv[1]:
	    f= [ "hiscoreCopy.pcl" ]
    if "2" in sys.argv[1]:
	    f= [ "hiscore2.pcl" ]
    if "ssm" in sys.argv[1]:
	    f= [ "ssm\*.pcl" ]
    if "pmodel" in sys.argv[1]:
	    f= [ "pmodel\?.py" ]
    if f == oldf:
        print ( "[fetch_hiscore] do not understand what you mean with '%s'. I only know of 'scan', 'states', 'copy', 'ssm'." % sys.argv[1] )
        sys.exit()
for i in f:
    cmd="scp wolfgan.waltenberger@clip-login-1:/scratch-cbe/users/wolfgan.waltenberger/rundir/%s ." % i
    print ( cmd )
    out = subprocess.getoutput ( cmd )
    print ( out )

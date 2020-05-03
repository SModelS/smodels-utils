#!/usr/bin/env python3

import subprocess, sys, copy

f= [ "hiscore.pcl" ]
if len(sys.argv)>1:
    oldf = copy.deepcopy(f)
    if "scan" in sys.argv[1]:
	    f= [ "scanM*.pcl", "mp*.pcl", "ssm*.pcl" ]
    if "mp" in sys.argv[1]:
	    f= [ "mp*.pcl" ]
    if "png" in sys.argv[1]:
	    f= [ "*.png" ]
    if "states" in sys.argv[1]:
	    f= [ "states.pcl" ]
    if "copy" in sys.argv[1]:
	    f= [ "hiscoreCopy.pcl" ]
    if "2" in sys.argv[1]:
	    f= [ "hiscore2.pcl" ]
    if "ssm" in sys.argv[1]:
	    f= [ "ssm*.pcl" ]
    if "pmodel" in sys.argv[1]:
	    f= [ "pmodel?.py" ]
    if f == oldf:
        print ( "[fetch_hiscore] do not understand what you mean with '%s'. I only know of 'scan', 'states', 'copy', 'ssm', 'png', 'pmodel'." % sys.argv[1] )
        sys.exit()
for i in f:
    cmd="scp wolfgan.waltenberger@clip-login-1:/scratch-cbe/users/wolfgan.waltenberger/rundir/%s ." % i
    print ( cmd )
    subprocess.run(cmd.split(" "), stderr=sys.stderr, stdout=sys.stdout)
    #out = subprocess.getoutput ( cmd )
    #print ( out )

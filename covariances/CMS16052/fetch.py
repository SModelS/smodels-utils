#!/usr/bin/env python3

import glob, os
import subprocess as commands

home=os.environ["HOME"]

dirs = glob.glob ( f"{home}/git/smodels-database-covariances" )
anaId="CMS-PAS-SUS-16-052-eff"

for dir in dirs:
    path = f"{dir}/13TeV/CMS/{anaId}"
    ars = glob.glob ( f"{path}/sr*" )
    nr = len ( ars ) 
    f=open("__init__.py","w")
    f.write ( "nSRs=%d\n" % nr )
    f.close()
    commands.getoutput ( f"cp {path}/sms.root ." )
    files = glob.glob ( f"{path}/validation/T*py" )
    print ( nr, dir, files )
    for f in files:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = f"cp {f} ./{topo}_{nr}.py"
        print ( cmd )
        commands.getoutput ( cmd )
        if os.path.exists ( f"./{topo}_all.py" ):
            commands.getoutput ( f"rm -f ./{topo}_all.py" )
        commands.getoutput ( f"ln -s ./{topo}_{nr}.py ./{topo}_all.py" )
    rootfiles = glob.glob ( f"{dir}/13TeV/CMS/{anaId}/validation/T*root" )
    for f in rootfiles:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = f"cp {f} ./{topo}.root"
        print ( cmd )
        commands.getoutput ( cmd )
    smsFile = f"{dir}/13TeV/CMS/{anaId}/sms.root"
    cmd = f"cp {smsFile} ."
    print ( cmd )
    commands.getoutput ( cmd )

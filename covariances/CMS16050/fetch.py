#!/usr/bin/env python3

import glob, os
import subprocess as commands

home=os.environ["HOME"]

#dirs = glob.glob ( "%s/git/smodels/test/covdb*" % home )
dirs = glob.glob ( f"{home}/git/smodels-database-covariances" )
anaId="CMS-SUS-16-050-eff"

for dir in dirs:
    # nr = dir [ dir.find("covdb")+5: ].replace("_","")
    # nr = 56
    #if len(nr)==0:
    #    continue
    ars = glob.glob ( f"{dir}/13TeV/CMS/CMS-SUS-16-050-eff/sr*" )
    nr = len ( ars ) 
    f=open("__init__.py","w")
    f.write ( "nSRs=%d\n" % nr )
    f.close()
    files = glob.glob ( f"{dir}/13TeV/CMS/CMS-SUS-16-050-eff/validation/T*py" )
    print ( nr, dir, files )
    for f in files:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = f"cp {f} ./{topo}_{nr}.py"
        print ( cmd )
        if not os.path.exists ( f"./{topo}_all.py" ):
            commands.getoutput ( f"ln -s ./{topo}_{nr}.py ./{topo}_all.py" )
        commands.getoutput ( cmd )
    rootfiles = glob.glob ( f"{dir}/13TeV/CMS/{anaId}/validation/T*root" )
    for f in rootfiles:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = f"cp {f} ./{topo}.root"
        print ( cmd )
        commands.getoutput ( cmd )

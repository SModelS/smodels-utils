#!/usr/bin/env python3

import glob, os
import subprocess as commands

home=os.environ["HOME"]

dirs = glob.glob ( "%s/git/smodels-database-develop" % home )
anaId="CMS-PAS-SUS-16-052-eff"

for dir in dirs:
    # nr = dir [ dir.find("covdb")+5: ].replace("_","")
    # nr = 56
    #if len(nr)==0:
    #    continue
    path = "%s/13TeV/CMS/%s/sr*" % (dir, anaId )
    ars = glob.glob ( path )
    nr = len ( ars ) 
    f=open("__init__.py","w")
    f.write ( "nSRs=%d\n" % nr )
    f.close()
    commands.getoutput ( "cp %s/sms.root ." % path )
    files = glob.glob ( "%s/validation/T*py" % ( path ) )
    print ( nr, dir, files )
    for f in files:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = "cp %s ./%s_%s.py" % ( f, topo, nr )
        print ( cmd )
        commands.getoutput ( cmd )
        if os.path.exists ( "./%s_all.py" % ( topo ) ):
            commands.getoutput ( "rm -f ./%s_all.py" % ( topo ) )
        commands.getoutput ( "ln -s ./%s_%s.py ./%s_all.py" % ( topo, nr, topo ) )

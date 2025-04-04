#!/usr/bin/env python3

import glob, os
import subprocess as commands

home=os.environ["HOME"]

dirs = glob.glob ( "%s/git/smodels-database-covariances" % home )
anaId="CMS-PAS-SUS-16-052-eff"

for dir in dirs:
    path = "%s/13TeV/CMS/%s" % ( dir, anaId )
    ars = glob.glob ( "%s/sr*" % path )
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
    rootfiles = glob.glob ( "%s/13TeV/CMS/%s/validation/T*root" % (dir, anaId ) )
    for f in rootfiles:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = "cp %s ./%s.root" % ( f, topo )
        print ( cmd )
        commands.getoutput ( cmd )
    smsFile = "%s/13TeV/CMS/%s/sms.root" % ( dir, anaId )
    cmd = "cp %s %s" % ( smsFile, "." )
    print ( cmd )
    commands.getoutput ( cmd )

#!/usr/bin/env python3

import glob, os
import subprocess as commands

home=os.environ["HOME"]

dirs = glob.glob ( "%s/git/smodels-database-covariances" % home )
anaId="CMS-PAS-SUS-16-052-best"

for dir in dirs:
    # nr = dir [ dir.find("covdb")+5: ].replace("_","")
    # nr = 56
    #if len(nr)==0:
    #    continue
    ars = glob.glob ( "%s/13TeV/CMS/%s/sr*" % (dir, anaId ) )
    nr = len ( ars ) 
    files = glob.glob ( "%s/13TeV/CMS/%s/validation/T*py" % (dir, anaId ) )
    print ( nr, dir, files )
    for f in files:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = "cp %s ./%s_%s.py" % ( f, topo, nr )
        print ( cmd )
        if not os.path.exists ( "./%s_all.py" % ( topo ) ):
            commands.getoutput ( "ln -s ./%s_%s.py ./%s_all.py" % ( topo, nr, topo ) )
        commands.getoutput ( cmd )
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

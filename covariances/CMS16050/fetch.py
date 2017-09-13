#!/usr/bin/python

import glob, os, commands

home=os.environ["HOME"]

dirs = glob.glob ( "%s/git/smodels/test/covdb*" % home )

for dir in dirs:
    nr = dir [ dir.find("covdb")+5: ].replace("_","")
    if len(nr)==0:
        continue
    files = glob.glob ( "%s/13TeV/CMS/CMS-PAS-SUS-16-050-eff/validation/T*py" % dir )
    # print ( nr, dir, files )
    for f in files:
        fname = os.path.basename ( f )
        tpos = fname.find ( "_" )
        topo = fname [ :tpos ]
        cmd = "cp %s ./%s_%s.py" % ( f, topo, nr )
        print ( cmd )
        commands.getoutput ( cmd )

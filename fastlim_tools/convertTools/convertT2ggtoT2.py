#!/usr/bin/env python

"""
created by: Wolfgang Waltenberger, adapted from convertT2toT2gg.py
Loops over all files and finds the T2gg efficiency maps from Fastlim.
Then redefine these maps as T2, where the constraint is [[['jet']],[['jet']]], 
instead of [[['jet']],[['jet']]].
"""

import os,sys,commands

def convert ( path = "." ):
    for root, dirs, files in os.walk( path ):
        # print root,dirs,files
        if not "-eff" in root: continue
        if "T2gg.effi" in files:
            cmd = f"mv {root}/T2gg.effi {root}/T2.effi"
            commands.getoutput ( cmd )
        if not "T2gg.txt" in files: continue
        ginfo = open(f"{root[:root.find('-eff') + 4]}/globalInfo.txt",'r')
        gdata = ginfo.read()
        ginfo.close()
        if not "fastlim" in gdata.lower(): continue
        t2f = open(f"{root}/T2gg.txt",'r')
        t2data = t2f.read()
        t2data = t2data.replace("txName: T2gg","txName: T2")
    #    t2data = t2data.replace("constraint: [[['jet']],[['jet']]]","constraint: [[['g']],[['g']]]")
        t2f.close()
        os.remove(f"{root}/T2gg.txt")
        t2f = open(f"{root}/T2.txt",'w')
        t2f.write(t2data)
        t2f.close()
        sys.exit()

convert ( "../../../smodels-database/" )

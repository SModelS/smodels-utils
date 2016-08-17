#!/usr/bin/env python

"""
created by: Wolfgang Waltenberger, adapted from convertT2toT2gg.py
Loops over all files and finds the T2gg efficiency maps from Fastlim.
Then redefine these maps as T2, where the constraint is [[['jet']],[['jet']]], 
instead of [[['jet']],[['jet']]].
"""

import os,sys

for root, dirs, files in os.walk("."):
    if not "-eff" in root: continue
    if not "T2gg.txt" in files: continue
    ginfo = open(root[:root.find("-eff")+4]+"/globalInfo.txt",'r')
    gdata = ginfo.read()
    ginfo.close()
    if not "fastlim" in gdata.lower(): continue
    t2f = open(root+"/T2gg.txt",'r')
    t2data = t2f.read()
    t2data = t2data.replace("txName: T2gg","txName: T2")
#    t2data = t2data.replace("constraint: [[['jet']],[['jet']]]","constraint: [[['g']],[['g']]]")
    t2f.close()
    os.remove(root+"/T2gg.txt")
    t2f = open(root+"/T2.txt",'w')
    t2f.write(t2data)
    t2f.close()


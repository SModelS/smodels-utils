#!/usr/bin/env python

"""
created by: Andre Lessa
Loops over all files and finds the T2 efficiency maps from Fastlim.
Then redefine these maps as T2gg, where the constraint is [[['g']],[['g']]], instead of [[['jet']],[['jet']]].
"""

import os,sys


for root, dirs, files in os.walk("."):
    if not "-eff" in root: continue
    if not "T2.txt" in files: continue
    ginfo = open(f"{root[:root.find('-eff') + 4]}/globalInfo.txt",'r')
    gdata = ginfo.read()
    ginfo.close()
    if not "fastlim" in gdata.lower(): continue
    t2f = open(f"{root}/T2.txt",'r')
    t2data = t2f.read()
    t2data = t2data.replace("txName: T2","txName: T2gg")
    t2data = t2data.replace("constraint: [[['jet']],[['jet']]]","constraint: [[['g']],[['g']]]")
    t2f.close()
    os.remove(f"{root}/T2.txt")
    t2f = open(f"{root}/T2gg.txt",'w')
    t2f.write(t2data)
    t2f.close()


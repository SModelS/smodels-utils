#!/usr/bin/env python3

""" small code snippet to get the PDGs of particles in the validation SLHA files.
Used for the Les Houches correlation study (WW). """

import glob
templatedir = "../slha/templates/"
files = glob.glob(f"{templatedir}/T*template" )

for fname in files:
    txname = fname.replace(".template","").replace(templatedir,"")
    print ( txname )
    with open ( fname ) as f:
        lines = f.readlines()
    pdgs={}
    for line in lines:
        line = line.strip()
        if not "~" in line:
            continue
        if "#" in line:
            line = line[:line.find("#")]
        if not "m" in line.lower():
            continue
        if "BR" in line:
            continue
        tokens = line.split ()
        if not tokens[1] in pdgs:
            pdgs[tokens[1]]=[]
        pdgs[tokens[1]].append ( str ( tokens[0] ) )
    for k,v in pdgs.items():
        print ( f"  `- {k}: {', '.join(v)}" )
    #print ( pdgs )

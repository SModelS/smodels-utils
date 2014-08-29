#!/usr/bin/env python

"""                                                                                   
.. module:: checkSynopses
   :synopsis: simple script that checks all python files in SModelS for
              a synopsis
                                                                                      
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>             
                                                                                      
""" 

import os
import setPath
from smodels_tools import SModelSTools

smodelsdir=SModelSTools.addSModelSPath()
print "checking SModelS at",smodelsdir
os.chdir ( smodelsdir )

failed=[]

for Dir in [ "experiment", "theory", "tools", "bin", "validation" ]:
    dDir=Dir+"/"
    files=os.listdir( Dir )

    for fle in files:
        if fle[-3:]!=".py":
            continue
        f=open(dDir+fle)
        lines=f.readlines()
        f.close()
        hasS=False
        for line in lines:
            if line.find("synopsis")>-1:
                hasS=True
                break
        # print dDir+fle,hasS
        if not hasS: 
            failed.append ( dDir+fle )

if len(failed)==0:
    print "No files with missing synopsis found."
else:
    print
    print "List of python files with missing :synopsis:"
    for i in failed:
        print i

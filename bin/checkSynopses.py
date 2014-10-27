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

def check ( dir, subdirs ):
    print "checking at",dir
    os.chdir ( dir )

    failed=[]

    for Dir in subdirs:
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
                failed.append ( dir+dDir+fle )

    if len(failed)==0:
        print "No files with missing synopsis found."
    else:
        print
        print "List of python files with missing :synopsis:"
        for i in failed:
            print i


tooldir=SModelSTools.installDirectory()

smodelsdir=SModelSTools.addSModelSPath()
dirs = [ "smodels/experiment", "smodels/theory", "smodels/tools", "bin" ]
check ( smodelsdir, dirs )

# check smodels-tools
check ( tooldir, [ "bin", "smodels_tools/helper", "smodels_tools/publication", \
       "smodels_tools/plotting", "smodels_tools/checks" ] )

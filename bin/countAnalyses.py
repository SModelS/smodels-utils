#!/usr/bin/env python

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

from __future__ import print_function
import setPath
import commands 
import sys
from short_descriptions import SDs
from smodels.experiment.databaseObj import Database
from smodels.tools.smodelsLogging import setLogLevel
setLogLevel("debug")
import IPython
    
def discussExperiment ( anas, experiment ):
    print ( experiment )
    print ( "%d analyses." % len(anas) )
    ul,em=0,0
    n_results = 0
    for expRes in anas:
        topos = set()
        if expRes.datasets[0].dataInfo.dataType=="upperLimit":
            ul+=1
        else:
            em+=1
        for dataset in expRes.datasets:
            for i in dataset.txNameList:
                topos.add ( i.id )
        n_results += len ( topos )
            
    print ( "%d upper limits" % ul )
    print ( "%d efficiency maps" % em )

    print ()

def main():
    db = Database ( '../../smodels-database/' )
    anas = db.getExpResults( useSuperseded=False )
    cms,atlas=[],[]
    for expRes in anas:
        Id=expRes.globalInfo.id
        if "CMS" in Id: cms.append ( expRes )
        if "ATLAS" in Id: atlas.append ( expRes )
    discussExperiment ( cms, "CMS" )
    discussExperiment ( atlas, "CMS" )
    
if __name__ == '__main__':
    main()    

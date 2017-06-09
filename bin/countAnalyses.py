#!/usr/bin/env python

"""
.. module:: countAnalyses
         :synopsis: Small script to produce a database statistics

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
    n_results_ul = 0
    n_results_em = 0
    for expRes in anas:
        topos = set()
        for dataset in expRes.datasets:
            for i in dataset.txnameList:
                if i.validated not in [ True, "N/A" ]:
                    continue
                topos.add ( i.txName )
        if expRes.datasets[0].dataInfo.dataType=="upperLimit":
            ul+=1
            n_results_ul += len ( topos )
        else:
            em+=1
            n_results_em += len ( topos )
        n_results += len ( topos )
            
    print ( "%d results total" % n_results )
    print ( "%d upper limits analyses" % ul )
    print ( "%d efficiency map analyses" % em )
    print ( "%d upper limits results" % n_results_ul )
    print ( "%d efficiency map results" % n_results_em )

    print ()

def mnot ( flag ):
    if flag: return ""
    return "not "

def filter ( anas, really=True ):
    if not really:
        return anas
    ret = []
    for ana in anas:
        contact = ""
        if hasattr ( ana.globalInfo, "contact" ):
            contact = getattr ( ana.globalInfo, "contact" ) 
        if "fastlim" in contact:
            continue
        ret.append ( ana )
    return ret

def main():
    db = Database ( '../../smodels-database/' )
    for superseded in [ False, True ]:
        print ()
        print ( "%s superseded" % mnot ( superseded ) )
        anas = db.getExpResults( useSuperseded=superseded )
        # for fastlim in [ True, False ]:
        #     print ( "filter fastlim: %d" % fastlim )
        anas = filter ( anas, True )
        cms,atlas=[],[]
        for expRes in anas:
            Id=expRes.globalInfo.id
            if "CMS" in Id: cms.append ( expRes )
            if "ATLAS" in Id: atlas.append ( expRes )
        discussExperiment ( cms, "CMS" )
        discussExperiment ( atlas, "ATLAS" )
    
if __name__ == '__main__':
    main()    

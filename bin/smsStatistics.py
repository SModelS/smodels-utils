#!/usr/bin/python

""" A simple tool that prints out results statistics.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import setPath
from smodels.experiment import smsResults

def count():
    #smsResults.ResultsForSqrts ( 0 )
    # smsResults.considerRuns()#if not all runs should be considered, give list of
    # runs to be considered as argument
    print "Base at",smsResults.smsHelpers.base
    # smsResults.smsHelpers.base = "/home/walten/git/smodels-database/"
    # smsResults.smsHelpers.base = "/afs/hephy.at/user/w/walten/public/sms/"
    smsResults.smsHelpers.runs = [ "2012", "8TeV", "ATLAS8TeV" ]


    All=smsResults.getAllResults()

    c={ "total":0, "public":0, "haveconstraint": 0, "2012": 0, "2011": 0,
            "ATLAS8TeV": 0, "8TeV":0, "checked": 0 }

    for analysis in All:
        for topo in All[analysis]:
            c["total"]+=1
            #if not smsResults.isPublic ( analysis ): continue
            #c["public"]+=1
            constr=smsResults.getConstraints ( analysis, topo )
            if not constr: continue
            c["haveconstraint"]+=1
            run=smsResults.getRun ( analysis )
            c[run]+=1
            #checked=smsResults.getCheckedBy ( analysis )
            #if checked: c["checked"]+=1

    return c

if __name__ == "__main__":
    c=count()
    print c["total"],"results total ..."
    print "... of which",c["public"],"are public ..."
    print "... of which",c["haveconstraint"],"have a SModelS description."
    print "... of which:"
    print c["2011"]+c["2012"]+c["8TeV"],"are CMS results"
    print c["ATLAS8TeV"],"are ATLAS results"
    print c["2011"]+c["2012"],"are 7 TeV results"
    print c["8TeV"]+c["ATLAS8TeV"],"are 8 TeV results"
    print c["checked"], "out of these", c["haveconstraint"],"have been verified so far"

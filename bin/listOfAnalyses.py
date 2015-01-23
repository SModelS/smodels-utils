#!/usr/bin/env python

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import setPath
# from smodels_utils import SModelSTools
from smodels_utils.helper import databaseBrowser
import logging
logger=logging.getLogger(__name__)

countResults=[0]
    
browser = databaseBrowser.Browser ( '../../smodels-database/' )
## browser = databaseBrowser.Browser ( )
f=open("ListOfAnalyses","w")

prettynames= { "thirdgen": "third generation", "hadronic": "hadronic production",
               "directslep": "direct slepton production", "eweakino": "weakino production" }

def yesno ( B ):
    if B in [ True, "True" ]: return "Yes"
    if B in [ False, "False" ]: return "No"
    return "?"

def header():
    f.write ( 
# """#acl +DeveloperGroup:read,write,revert -All:write,read Default 
# <<LockedPage()>>
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default 

= List Of Analyses =
List of analyses and topologies in the SMS results database that has been used in [[http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5|EPJC May 2014, 74:2868]].
It has been created with the [[http://smodels.hephy.at/gitweb/?p=smodels-utils.git;a=blob;f=bin/listOfAnalyses.py;h=33bc2e9b0eb1854f475b847928a11a1ae6d3098e;hb=refs/heads/develop|listOfAnalyses.py]] tool. 
The list has been created from the database version `%s`.
There is also an SmsDictionary.

 * Has Condition: lists, whether a special condition is required in order for the constraint to be applicable.
 * Data published in digital form: has the experiment published the data in digital form? (e.g. as a ROOT file, or a HEPDATA table).
 * Expected upper limits: has the experiment also published a histogram with the '''expected''' upper limits?

To experiment: [[#CMS|CMS]], [[#ATLAS|ATLAS]]

""" % browser.databaseVersion )

def xsel():
    import os
    cmd="cat ListOfAnalyses | xsel -i"
    os.system ( cmd )
    print cmd

def experimentHeader ( experiment ):
    f.write ( "\n" )
    f.write ( "== %s ==\n" % experiment )
    f.write ( "<<Anchor(%s)>>\n" % experiment )


def writeSection ( experiment, section, analyses ):
    f.write ( "=== %s ===\n" % prettynames[section] )
    f.write ( "<<Anchor(%s%s)>>\n" % ( experiment, section ) )
    f.write ( "\n" )
    for colheader in [ "Analysis", "#", "Topology", "Constraint", "Has Condition?", \
        "Data published in digital form?", "Expected upper limits?" ]:
        f.write ( "||<#EEEEEE>'''%s''' " % colheader )
    f.write ( "||\n" )
    # f.write ( "||'''Analysis''' || '''#''' ||'''Topology''' ||'''Constraint''' ||'''Has Condition?''' ||'''Data published in digital form?''' ||\n" )
    names=analyses.keys()
    names.sort()
    for ananame in names:
        ana=analyses[ananame]
        if not ana.checked:
            continue
        if ana.private:
            continue
        anaurl=ana.url
        topos=ana.topologies
        anatopos=[]
        for topo in topos:
            otopo = browser.expTopology ( topo )
            if otopo.category != section:
                continue
            constr=otopo.constraints ## check if we have a constraint
            has_constr=False
            for i in constr:
                if i in [ "", "Not yet assigned" ]:
                    continue
                has_constr=True
            if has_constr:
                anatopos.append ( topo )
        if len(anatopos)==0:
            continue
        span="<:>"
        if len(anatopos)>1:
            span="<:|%d>" % len(anatopos)
        ananameb=ananame.replace("_"," ")
        # f.write ( "|| || || || || || || ||\n" )
        f.write ( "||||||||||||||||\n" )
        f.write ( "||%s [[%s|%s]]<<BR>>%d TeV<<BR>> %s fb^-1^" % \
                  ( span,anaurl,ananameb, int(float(ana.sqrts)), ana.lumi ) )
        for topo in anatopos:
            topolink='{{http://smodels.hephy.at/feyn/%s_feyn.png||height="150"}}' \
                     % topo
            #otopo=browser.expTopology ( topo )
            #constr=""
            #container=[] ## dont list twice
            from smodels.experiment import smsResults
            constrs=smsResults.getConstraints ( ananame, topo )
            #print constrs,type(constrs)
            #for i in otopo.constraints:
            #    if i in [ "", "Not yet assigned" ]: continue
            #    ii=i.replace("'","").replace(" ","")
            #    if ii in container: continue
            #    constr+="~+[+~`%s`~+]+~, " % ( ii[1:-1] )
            #    container.append ( ii )
            #constr=constr[:-2]
            if constrs in [ None, "", "None" ]: continue
            constr=constrs.replace("'","").replace(" ","")
            if constr[0]=="[" and constr[-1]=="]":
                constr="~+[+~`%s`~+]+~" % ( constr[1:-1] )
            else:
                constr="`%s`" % constr
            mycond=smsResults.getConditions ( ananame, topo )
            hascond=True
            if mycond in [ "None", None, "" ]: hascond=False
            datapub=ana.publishedData
            countResults[0]=countResults[0]+1
            res=browser.expResult ( ananame, topo )
            # expctd=res.hasExpectedUpperLimits
            expctd=False
            f.write ( "|| %d || %s || %s || %s || %s || %s||\n" \
                      % ( countResults[0], topolink, constr, \
                          yesno(hascond), yesno(datapub), yesno(expctd) ) )

def writeExperiment ( experiment ):
    experimentHeader ( experiment )
    anas = browser.getAnalyses()
    categories=set()
    manas={}

    for sana in anas:
        ana = browser.expAnalysis ( sana )
        if ana.experiment != experiment:
            continue
        for stopo in ana.topologies:
            topo = browser.expTopology ( stopo )
            cats = topo.category
            if cats in [ None, "" ]: continue
            for cat in cats.split(","):
                spcat = cat.replace(" ","")
                categories.add( spcat )
                if not spcat in manas:
                    manas[spcat]={}
                manas[spcat][ana.name]=ana
    s="Section: "
    for cat in categories:
        s+= "[[#%s%s|%s]], " % ( experiment, cat, prettynames[cat] ) 
    f.write ( "%s\n\n" % s[:-2] )
    for cat in categories:
        writeSection ( experiment, cat, manas[cat] )

def main():
    header()
    browser.verbosity='error'
    print "base=",browser.base
    experiments=[ "CMS", "ATLAS" ]
    for experiment in experiments:
        writeExperiment ( experiment )

    xsel()
    
if __name__ == '__main__':
    main()    

#!/usr/bin/env python

"""
.. module:: smsDictionary
         :synopsis: Small script to produce the SmsDictionary wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import setPath
from smodels_utils import SModelSTools
from smodels_utils.helper import databaseBrowser
from smodels_utils.plotting import feynmanGraph
from smodels.theory import element

import logging
logger=logging.getLogger(__name__)
    
browser = databaseBrowser.Browser ( '../../smodels-database/' )
## browser = databaseBrowser.Browser ( )
f=open("SmsDictionary","w")

shortnames={ "directslep": "weakinos", "hadronic": "colored",
             "thirdgen": "third", "eweakino": "weakinos",
             "hadronic, thirdgen": "colored", "None": "none",
             "not yet assigned": "none" }
longnames={ "sleptons": "sleptons", "colored": "colored production",
            "third": "third generation", "weakinos": "weakinos and sleptons",
            "none": "not categorized" }
categoryorder=( "colored", "third", "weakinos", "none" )

def header( categories ):
    f.write ( 
##"""#acl +DeveloperGroup:read,write,revert -All:write,read Default 
## <<LockedPage()>>
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default 

= SMS dictionary =
This page intends to collect information about how we map the SModelS description of 
events onto the Tx nomenclature. It has been created with the [[http://smodels.hephy.at/gitweb/?p=smodels-utils.git;a=blob;f=bin/smsDictionary.py;h=25451211ccf1d38e98c34b9d42e44deb39c6d6ea;hb=refs/heads/develop|smsDictionary.py]] tool. 

The list has been created from the database version %s.

There is also a ListOfAnalyses.

""" % browser.databaseVersion )
    ret="The dictionary is split up by production:  "
    for cat in categories:
        ret+= "[[#%s|%s]], " % ( cat, longnames[cat] )
    f.write ( ret[:-2]+"\n" )


def footer():
    f.write (
"""

Obs: Each "()" group corresponds to a branch

"""
)

def xsel():
    import os
    cmd="cat SmsDictionary | xsel -i"
    os.system ( cmd )
    print cmd

def categoryHeader ( shortname, longname ):
    f.write ( "\n" )
    f.write ( "== %s ==\n" % longname )
    f.write ( "<<Anchor(%s)>>\n" % shortname )
    # f.write ( '||<tableclass="sortable"> Tx Name || Topology || Graph || Results ||\n' )
    for header in [ "#", "Tx", "Topology", "Graph", "Results" ]:
        f.write ( "||<#EEEEEE:> '''%s''' " % header )
    f.write ( "||\n" )
    ## f.write ( '||<tableclass="sortable"> Tx Name || Topology || Graph || Results ||\n' )

topoCounter=[0]

def writeTopo ( topo ):
    # print "topo",topo.name,len(topo.analyses)
    if len(topo.analyses)==0: return
    ## count number of legit analyses
    counter=0
    for ana in topo.analyses:
        oana=browser.expAnalysis ( ana ) ## get the object
        if oana.private:
            continue
        if oana.checked==False:
            continue
        counter+=1
    if counter==0:
        logger.info ( "couldnt find any checked analysis for %s. Skipping." % topo )
        return

    name=topo.name
    rname=name
    if name in [ "T7ChiSlep", "T8ChiSlep" ]:
        rname="!"+name
    if name == "T2_OneSq":
        rname="T2_!OneSq"
    constr="Not yet assigned"
    for c in topo.constraints:
        ##if name=="T1tttt":
            ## print "c=",c,type(c),len(c)
        if c.find("Not yet assigned")>-1 or c=="":
            continue
        constr=str ( c ).replace('"',"")
        break
    first=constr
    if first.find(" + ")>-1.:
        first=first[:first.find(" + ")]
    if first.find("]+[")>-1.:
        first=first[:first.find("]+[")+1]
    if first.find("*")>-1.:
        first=first[first.find("*")+1:]
    first=first.replace("(","").replace(")","")

    if first.find("Not yet assigned")>-1:
        logger.error ( "%s not yet assigned" % (name) )
        return
    #    print "not yet assigned:", topo.constraints
    #    first="[[[]],[[]]]"
    if first in [ "", "None", "not yet assigned" ]:
        logger.error ( "%s: first is empty: %s" % (name,topo.constraints) )
        return
    print "name",name,"first",first
    constro=eval(first)
    # print "   `-",constro
    v1,v2=len(constro[0])+1,len(constro[1])+1
    i1,i2="(","("
    for i in constro[0]:
        i1+="%d," % len(i)
    i1=i1[:-1]+",0)"
    for i in constro[1]:
        i2+="%d," % len(i)
    i2=i2[:-1]+",0)"
    topoCounter[0]+=1
    f.write ( "||%d||<:>'''%s'''<<Anchor(%s)>>" % ( topoCounter[0], rname, name ) )
    f.write ( "||vertices: (%d)(%d) <<BR>>  " % ( v1,v2) )
    f.write ( "insertions: %s%s <<BR>> " % ( i1,i2 ) )
    # f.write ( "(jet)(jet) <<BR>>" )
    constr=constr.replace("'","")
    # constr=constr.replace("[[","(").replace("]]",")")
    #constr=constr.replace("[","(").replace("]",")")
    constr="`%s`" % constr 
    f.write ( constr )
    f.write ( '||{{http://smodels.hephy.at/feyn/%s_feyn.png||width="150"}}' % name )
    f.write ( "|| " )
    createFeynGraph=True
    if createFeynGraph:
        print "name,constr=",name,constr
        c=constr
        p=c.find("]+")
        if p>-1:
            c=c[:p+1]
        p=c.find("] +")
        if p>-1:
            c=c[:p+1]
        c=c.replace("71.*","").replace("(","").replace(")","")
        feynfile=name+"_feyn.png"
        print "drawing",feynfile,"from",c
        e=element.Element(c)
        feynmanGraph.draw ( e, feynfile, straight=False, inparts=True, verbose=False )
    for experiment in [ "CMS", "ATLAS" ]: 
        # order by experiment
        for ana in topo.analyses:
            oana=browser.expAnalysis ( ana ) ## get the object
            ## print "ana",ana,oana.experiment,oana.checked,oana.url
            if oana.experiment != experiment:
                continue
            ## print oana.name,"private",type(oana.private),oana.private
            if oana.private:
                logger.warn ( "%s is marked as private." % ana )
                continue
            if oana.checked==False:
                continue
            url=oana.url
            if url==None:
                continue
            if url.find(", ")>-1:
                url=url[:url.find(", ")-1]
            f.write ( "[[%s|%s]]<<BR>>" % ( url, ana.replace("_"," ") ) )
    f.write ( "||\n" )

def topoCmp ( x, y ):
    """ order topology names canonically, first by length
        of name, then by alphabet """
    if x.name == y.name:
        return 0
    if len(x.name) < len(y.name):
        return -1
    if len(x.name) > len(y.name):
        return 1
    if x.name < y.name:
        return -1
    return 1

def main():
    browser.verbosity='error'
    print "Base=",browser.base
    topos = browser.getTopologies()
    categories={}
    for toponame in topos:
        topo = browser.expTopology ( toponame )
        scat=topo.category
        if scat in [ None, "" ]:
            scat="None"
        cat=shortnames [ scat ]
        if not cat in categories: categories[cat]=[]
        categories[cat].append ( topo )
    header( categories.keys() )

    for cat in categoryorder:
        if not cat in categories:
            continue
        topos = categories[cat]
        topos.sort ( topoCmp )
        categoryHeader ( cat, longnames[cat] )
      #  print cat,">>",
        for topo in topos:
     #       print topo.name," ",
            writeTopo ( topo )
    #    print
    footer()
    xsel()

    
if __name__ == '__main__':
    main()    

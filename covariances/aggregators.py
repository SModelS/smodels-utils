#!/usr/bin/env python3

""" methods revolving around aggregations """


import sys, numpy
from math import sqrt
from smodels.experiment.databaseObj import Database
from smodels_utils.helper import various
import IPython
import pickle
import tempfile
import os
import argparse
import cov_helpers
from typing import Dict, List, Union

def getDatasets( result, addReverse = True, verbose = False ):
    """ given an experimental result, return datasets and possibly
        dictionary of comments
    :param addReverse: if True, then also add reverse lookup
    """
    datasets,comments={},{}
    for _,ds in enumerate ( result.datasets ):
        i=_ + 1
        datasets[i]=ds.dataInfo.dataId
        comments[i]=ds.dataInfo.dataId
        if hasattr ( ds.dataInfo, "comment" ):
            comments[i]=ds.dataInfo.comment
        if verbose:
            print ( f"[{i}]: {comments[i]}" )
        if addReverse:
            datasets[ ds.dataInfo.dataId ] = i
    return datasets, comments

def retrieve ( fname ):
    """ get a dictionary of scores of signal regions, for one validation file
    """
    f=open(fname,"rt" )
    globalsParameter = {}
    exec ( f.read(), globalsParameter )
    f.close()
    ret = {}
    n = len ( globalsParameter["validationData"] )
    for pt in globalsParameter["validationData"]:
        if 'leadingsDSes' in pt: # typo in py file
            for idx,(k,v) in enumerate(pt["leadingsDSes"]):
                if not v in ret:
                    ret[v]=0
                ret[v]+=1000./(n*(idx+1)**2)
        if 'leadingDSes' in pt:
            for idx,(k,v) in enumerate(pt["leadingDSes"]):
                if not v in ret:
                    ret[v]=0
                ret[v]+=1000./(n*(idx+1)**2)
    return ret

def useNames ( aggs, datasets ):
    """ given lists of lists of indices, return lists of lists of
        dataset names """
    ret = []
    for agg in aggs:
        tmp = []
        for i in agg:
            tmp.append ( datasets[i] )
        ret.append ( tmp )
    return ret

def oneIndex ( aggs ):
    """ move all from 0-indexed to 1-indexed, i.e. add one to all elements """
    ret = []
    for a in aggs:
        tmp = []
        for i in a:
            # tmp.append ( "SR%d" % ( i+1 ) )
            tmp.append ( i+1 )
        ret.append ( tmp )
    return ret

def checkIfToAdd ( index : int, agg : list, frac : float, corrmatrix : list ):
    """ check if to add index to aggregation list agg,
    :param index: the index to be added
    :param agg: list of aggregated indices
    :param frac: threshold on correlation, aggregate if all correlations are above it
    :param corrmatrix: correlation matrix to look up the correlations
    """
    # a minimum spanning tree is implemented as follows:
    return True

    # print ( f"shall we add {index} to {agg}?" )
    # print ( f"covs are: {[ corrmatrix[ index ][x] for x in agg ] }" )
    ## for now we implement a maximum spanning tree, i.e. add index only to agg
    ## if *all* correlations are above threshold
    allAbove = True
    for x in agg:
        corr = corrmatrix[ index ][x]
        if corr < frac:
            allAbove = False
            break
    return allAbove

def retrieveEMStats ( database, analysis ):
    """ see if we can retrieve data from a statsEM.py file.
        helpful for aggregation by name
    :param database: path to database
    :param analysis: ana id, e.g. CMS-SUS-19-006
    """
    path = various.getPathName ( database, analysis )
    path = os.path.join ( path, "orig", "statsEM.py" )
    if not os.path.exists ( path ):
        return {}
    f = open ( path, "rt" )
    txt = f.read()
    f.close()
    D = eval ( txt )
    return D

def obtainDictFromComment ( comment : str, analysis : str, level : int=1 ) -> Dict:
    """ given the comment, obtain a dict with relevant analysis specific info,
        for clustering 
    :param comment: the comment field of the SR, e.g. 
    "ML_A3l_2016_0 (AccEff_MultiLep,CMS-SUS-19-012)"
    :param level: level of detail. 1 is course, higher is more aggregated regions
    """
    D = {}
    if "CMS-SUS-21-008" in analysis:
        p1 = comment.rfind("(")
        tbranch = comment[p1:].replace("(","").replace(")","")
        comment = comment[:p1-1]
        branchvalues = tbranch.split(",")
        branch,subanalysis = branchvalues
        tokens = comment.split("_")
        lastnr = None
        try:
            lastnr = int ( tokens[-1] )
        except Exception as e:
            pass
        if lastnr != None:
            D["triplet"] = lastnr % level
        D["branch"] = branch
        year = None
        # print ( tokens )
        if "201" in tokens[2]:
            year = tokens[2]
        if "SR" in tokens[1] or "bVeto" in tokens[1] or "nj" in tokens[1]:
            D["subbranch"]=f"{tokens[1]}_{tokens[2]}"
            D["unique"]=True
        #if "SR" in tokens[1]:
        #    D["subbranch"]=tokens[1]
        if tokens[1].endswith("l"):
            D["subbranch"]=tokens[1]
        if year is not None:
            D["year"] = year
    if "CMS-SUS-19-012" in analysis:
        p1 = comment.rfind("(")
        tbranch = comment[p1:].replace("(","").replace(")","")
        comment = comment[:p1-1]
        branchvalues = tbranch.split(",")
        branch,subanalysis = branchvalues
        tokens = comment.split("_")
        lastnr = None
        try:
            lastnr = int ( tokens[-1] )
        except Exception as e:
            pass
        if lastnr != None:
            if level == 0:
                D["nr"]=lastnr
            else:
                D["triplet"] = lastnr % level
        D["branch"] = branch
        year = None
        if False and "201" in tokens[2]:
            year = tokens[2]
        if tokens[1].endswith("l"):
            D["subbranch"]=tokens[1]
        if year is not None:
            D["year"] = year
        # print ( f"@@0 comment {comment} -> D {D}" )
    if "CMS-SUS-19-006" in analysis:
        tokens = comment.split("_")
        D["jets"]= int ( tokens[1].replace("Njet","") )
        D["b"] = int ( tokens[2].replace("Nb","") )
        # D["HT"]= int ( tokens[3].replace("HT","") )
    if "CMS-SUS-16-050" in analysis:
        tokens = comment.split("_")
        nt = tokens[0].replace("Ntops=","")
        if nt == "Ntops>=3":
            nt="3"
        D["ntops"]= int ( nt )
        nb = tokens[1].replace("Nbjets=","")
        if nb == "Nbjets>=3":
            nb=3
        D["b"] = int ( nb )
        mt2 = tokens[2].replace("MT2=","").replace("MT2>=","")
        mt2 = mt2.replace("HT","10000").replace("=","").replace(">","")
        p = mt2.find("-")
        if level>1:
            D["MT"]=int ( mt2[:p] )
    if "CMS-SUS-16-048" in analysis:
        tokens = comment.split("_")
        D["ewkino"]=-1
        if tokens[0]=="stop":
            D["ewkino"]=0
        if tokens[0]=="Ewkino":
            D["ewkino"]=1
        D["met"]=-1
        if tokens[1]=="lowMET":
            D["met"]=0
        if tokens[1]=="medMET":
            D["met"]=1
        if tokens[1]=="highMET":
            D["met"]=2
        pt = tokens[3]
        p = pt.find("to")
        pt = int ( pt[:p] )
        # D["pt"]=pt
        # print ( "tokens", tokens, "D", D )
    if "CMS-SUS-16-039" in analysis:
        tokens = comment.split("_")
        # print ( tokens )
        #D["jets"]= int ( tokens[1].replace("Njet","") )
        mll = tokens[1].replace("Mll","")
        p1 = mll.find("to")
        D["mll"] = int ( mll[:p1] )
        mt = tokens[2].replace("MT","")
        p1 = mt.find("to")
        # D["MT"] = int ( mt[:p1] )
        met = tokens[3].replace("MET","")
        p1 = met.find("to")
        # D["MET"] = int ( met[:p1] )
    if len(D)==0:
        print ( f"[aggregators.py] ERROR: empty dictionary, implement for {analysis}, comment was {comment}!" )
        sys.exit()
    return D

def getExpResult ( database, analysis ):
    print ( "[aggregators.py] instantiating database ", end="...", flush=True )
    d=Database( database )
    #if analysis.endswith ( "-eff" ):
    #¤    analysis = analysis.replace("-eff","")
    ids = [ analysis ]
    print ( "done." )
    aggs = []
    results=d.getExpResults( analysisIDs=ids, dataTypes=["efficiencyMap"],
                             useNonValidated=True )
    if len(results)==0:
        print ( f"[aggregators.py] could not find result '{analysis}' in database '{database}'." )
        sys.exit()
    return results[0]

def toLetter ( index : int ) -> str:
    """ translate an index to a letter:
    0 -> a, 1 -> b, 25 -> z, 26 -> A, ... 
    """
    if True:
        return str(index)
    if index <= 25:
        return chr(97+index)
    return chr(65+index-26)

def aggregateByNames ( database, analysis, drops, exclusives, level, verbose ):
    """ run the aggregator based on SR names
    :param database: path to database
    :param analysis: ana id, e.g. CMS-SUS-19-006
    :param drop: list of indices to drop from aggregation entirely
    :param exclusives: list of indices to not aggregate, but keep as individual
                       SRs
    :param level: level of detail. 1 is course, higher is more aggregated regions
    """
    result  = getExpResult ( database, analysis )
    datasets, comments = getDatasets( result, addReverse=False, verbose = verbose )
    filtered = {}
    dropped, aggs = [], []
    droppedD = []
    D = {}
    for srnr, srname in datasets.items():
        if srnr in drops:
            droppedD.append ( srname )
            continue
        if srnr in exclusives:
            D.append ( [ srname ] )
            continue
        filtered[srnr] = srname
    aggs, aggnames = {}, {}
    srprefixes = {}
    for srnr,srname in filtered.items():
        commdict = obtainDictFromComment ( comments[srnr], analysis, level )
        scomment = str(commdict)
        if not scomment in aggnames.keys():
            p1 = srname.find("_")
            srprefix = srname[:p1]
            if not srprefix in srprefixes:
                srprefixes[srprefix]=[]
            newname=f"{srprefix}_{toLetter(len(srprefixes[srprefix]))}"
            if "unique" in commdict.keys():
                newname = srname
            srprefixes[srprefix].append(newname)
            #newname=f"ar{len(aggnames)}"
            aggnames[scomment]=newname
            aggs[newname]=[]
        name = aggnames[scomment]
        aggs[name].append ( srname )
    return aggs, droppedD

def aggregateByCorrs ( database, analysis, drop, exclusives, corr, verbose ):
    """ run the aggregator based on correlations
    :param database: path to database
    :param analysis: ana id, e.g. CMS-SUS-19-006
    :param drop: list of indices to drop from aggregation entirely
    :param exclusives: list of indices to not aggregate, but keep as individual
                    SRs
    :param corr: cut on correlation
    """
    result = getExpResult ( database, analysis )

    cov = result.globalInfo.covariance
    corrmatrix = cov_helpers.computeCorrelationMatrix ( cov )
    n=len(cov)
    # n=2

    pairs = {}

    for i in range(n):
        for j in range(i+1,n):
            cor = cov[i][j]/sqrt(cov[i][i]*cov[j][j] )
            # print ( "cov[%d,%d]=%f" % ( i+1,j+1, cor) )
            pairs[cor] = [i,j]
            # pairs[cor] = [i+1,j+1]

    corrs = list(pairs.keys())
    corrs.sort(reverse=True)

    done = []
    aggs = []
    excls = []
    dropped = []

    frac=corr

    if drop != None:
        for i in drop:
            if type(i) in [ list, tuple ]:
                done.append ( i[0]-1 )
                dropped.append ( i[0] )
            if type(i) in [ int ]:
                done.append ( i-1 )
                dropped.append ( i )

    if exclusives != None:
        for i in exclusives:
            i0 = i
            if type(i) in [ list, tuple] :
                i0 = i[0]
            done.append ( i0-1 )
            excls.append ( i0-1 )
            aggs.append ( [ i0-1 ] )

    for k in corrs:
        #if k < .1:
        #    break
        v = pairs[k]
        # print ( "%.2f: %s" % ( k, v ) )
        if v[0] in done and v[1] in done:
            ## all taken care of
            continue
        if not v[0] in done and not v[1] in done:
            if k > frac:
                ## a virgin pair. add as new aggregate region
                done.append ( v[0] )
                done.append ( v[1] )
                aggs.append ( v )
            else:
                done.append ( v[0] )
                done.append ( v[1] )
                aggs.append ( [ v[0] ] )
                aggs.append ( [ v[1] ] )
        if v[0] in done and not v[1] in done:
            if k > frac and not v[1] in excls and not v[0] in excls:
                ## v0 is already in a region. lets add v1.
                for agg in aggs:
                    if v[0] in agg and checkIfToAdd ( v[1], agg, frac, corrmatrix ):
                        ## lets assume yes
                        done.append ( v[1] )
                        agg.append ( v[1] )
            else: ## we cant add v1
                done.append ( v[1] )
                aggs.append ( [ v[1] ] )
        if v[1] in done and not v[0] in done:
            if k > frac and not v[0] in excls and not v[1] in excls:
                ## v1 is already in a region. can we add v0?
                for agg in aggs:
                    if v[1] in agg and checkIfToAdd ( v[0], agg, frac, corrmatrix ):
                        done.append ( v[0] )
                        agg.append ( v[0] )
            else:
                done.append ( v[0] )
                aggs.append ( [ v[0] ] )

    for a in aggs:
        a.sort()
    aggs.sort()
    aggs = oneIndex ( aggs )

    return aggs, dropped

def describeDict ( aggs : Dict, dropped : List, n : Union[None,int] =None ):
    c=set()
    for aggname, srs in aggs.items():
        for sr in srs:
            c.add ( sr )
    nregions, nexclusives = len(c), 0
    if n != None:
        nregions = n
    for i in aggs:
        if len(i)==1:
            nexclusives+=1
    print ( f"# {' '.join(sys.argv)}" )
    print ( f"# {nregions} regions -> {len(aggs)} agg regions with {len(dropped)} dropped and {nexclusives} exclusives:" )
    print ( "aggregates={", end="" )
    for aggname, srs in aggs.items():
        print ( f"'{aggname}': {srs}," )
    print ( "}" )

def check ( aggs, drops, n ):
    """ check if every SR is accounted for """
    srs = set()
    for name,agg in aggs.items():
        for a in agg:
            srs.add ( a )
    if len(srs)==n:
        return True
    print ( f"[aggregators] mismatch in number of SRs: {len(srs)}!={n}" )
    sys.exit()

def describe ( aggs, dropped, n=None ):
    if type(aggs)==dict:
        return describeDict ( aggs, dropped, n=None )
    c=set()
    for i in aggs:
        for j in i: c.add ( j )
    # oaggs = oneIndex ( aggs )
    print ( f"[aggregators.py] largest aggregation has {max( [ len(x) for x in aggs ] )} elements" )
    nregions, nexclusives = len(c), 0
    if n != None:
        nregions = n
    for i in aggs:
        if len(i)==1:
            nexclusives+=1
    print ( f"# {' '.join(sys.argv)}" )
    print ( f"# {n} regions -> {len(aggs)} agg regions with {len(dropped)} dropped and {nexclusives} exclusives:" )
    print ( f"aggregates={aggs}" )
    # print ( "with names", useNames ( aggs, getDatasets() ) )

def main():
    """ redundant main function, see aggregate.py for usage """
    ap = argparse.ArgumentParser( description= "find aggregate regions based on correlations." )
    ap.add_argument('-a','--analysis',help="name of analysis to discuss [CMS-SUS-19-006-ma5]",
                    default = "CMS-SUS-19-006-ma5", type=str )
    ap.add_argument('-c','--corr',help="correlation needed to cluster [.5]",
                    default = .5, type=float )
    ap.add_argument( '-t','--takeout',help="dont cluster these SRs", nargs="*",
                     type=int, action="append" )
    ap.add_argument( '-d','--drop',help="drop these SRs", nargs="*",
                     type=int, action="append" )
    ap.add_argument('-D','--database',help="path to database [../../smodels-database]",
                    default = "../../smodels-database", type=str )
    args = ap.parse_args()
    aggs, dropped = aggregateByCorrs ( args.database, args.analysis, args.drop, args.takeout, args.corr )
    describe ( aggs, dropped )

if __name__ == "__main__":
    main()

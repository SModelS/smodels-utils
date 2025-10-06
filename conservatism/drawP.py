#!/usr/bin/env python3

import numpy as np

def filterByAnaId ( data : list, dropThese : list ) -> list:
    """ filter by analysis ids 
    :param dropThese: list of analysis ids to drop
    """
    ret = []
    outfile = "pvalues.png"
    for entry in data:
        if entry["id"] in dropThese:
            continue
        else:
            ret.append ( entry )
    return ret

def filterByBG ( data : list ) -> list:
    """ filter the data by expected background yield """
    bgmin = 2.5
    ret = []
    for entry in data:
        if entry["bg"]>bgmin:
            ret.append ( entry )
    return ret

def splitBySqrts ( data : list ) -> dict:
    """ split up data by sqrts """
    ret = {}
    from smodels_utils.helper.various import getSqrts
    # from smodels_utils.helper.various import getSqrts, getCollaboration
    for entry in data:
        sqrts = getSqrts ( entry["id"] )
        ssqrts = f"{sqrts} TeV"
        if not ssqrts in ret:
            ret[ssqrts]=[]
        ret[ssqrts].append ( entry )
    return ret

def splitByCollaboration ( data : list ) -> dict:
    """ split up data by collaboration """
    ret = {}
    from smodels_utils.helper.various import getCollaboration
    for entry in data:
        coll = getCollaboration ( entry["id"] )
        if not coll in ret:
            ret[coll]=[]
        ret[coll].append ( entry )
    return ret
    
def getPValues ( data : dict, statmodel : str ) -> dict:
    """ extract the right p-values from the entire entries """
    ret = {}
    for label, xdata in data.items():
        if not label in ret:
            ret[label] = []
        for entry in xdata:
            ret[label].append ( entry[ f"p_{statmodel}" ] )
    return ret

def drawP ( args : dict ):
    """ draw a histogram of the pvalues 
    :args dictionary:
    :iparam fudge: draw for that fudge factor
    :iparam inputFile: path to input data create by createData.py
    :iparam outfile: png file
    :iparam statmodel: norm or lognorm for nuisances
    """
    with open(args["inputfile"],"rt") as f:
        data = eval(f.read())
    fudge = args["fudge"]
    statmodel = args["statmodel"]
    dropThese = []
    monojets = [ "CMS-EXO-20-004", "ATLAS-EXOT-2018-06" ]
    dropThese.append  ( x for x in monojets )
    dropThese.append ( [ "ATLAS-SUSY-2018-16-hino", "ATLAS-SUSY-2018-16", \
                  "ATLAS-SUSY-2018-42" ] )
    dropThese.append ( "ATLAS-SUSY-2017-03" )
    dropThese.append ( "CMS-SUS-20-004" )
    dropThese = []
    data = filterByAnaId ( data[fudge], dropThese )
    # data = data[fudge]
    data = filterByBG ( data )
    splitdata = splitBySqrts ( data )
    splitdata = splitByCollaboration ( data )
    pvalues = getPValues ( splitdata, statmodel )
    from matplotlib import pyplot as plt
    bins = np.linspace(0,1,args["nbins"]+1)
    for label, ps in pvalues.items():
        plt.hist ( ps, label = label, bins = bins )
    plt.legend()
    plt.title ( f"Distribution of p-values, fudge={fudge:.1f}" )
    plt.xlabel ( "p-values" )
    plt.ylabel ( "occurrence" )
    outfile = args["outputfile"].replace("@@FUDGE@@",str(fudge))
    outfile = outfile.replace("@@STATMODEL@@",statmodel)
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=
            "Produces p-values plots for a specific fudge factor")
    ap.add_argument('-i', '--inputfile',
            help='input file [data.dict]', default='data.dict' )
    ap.add_argument('-o', '--outputfile',
            help='output file [pvalues@@FUDGE@@.png]', 
            default='pvalues@@FUDGE@@_@@STATMODEL@@.png' )
    ap.add_argument('-s', '--statmodel',
            help='statmodel norm or lognorm [norm]', 
            default='norm' )
    ap.add_argument('-f', '--fudge', type=float,
            help='fudge factor [1.0]', default=1.0 )
    ap.add_argument('-n', '--nbins', type=int,
            help='number of bins in histogram [10]', default=10)
    args = ap.parse_args()
    drawP( vars(args) )

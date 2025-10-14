#!/usr/bin/env python3
# coding: utf-8

""" a script that creates the data for the conservatism plots """

import scipy.stats
import numpy as np

import sys
sys.path.insert(0,"../../protomodels/")

hasWarned = { "signals": 0 }

def computePValues( data : dict, fudge : float,
       nmin : int = 50000, nmax : int = 100000 ) -> dict:
    """ compute p-values
    :param fudge: fudge factor
    :param nmin: minimum number of toys
    :param nmax: maximum number of toys

    :returns: dictionary, with id, obs, etc and also p_norm p_lognorm
    """
    ret = []
    for dataID in data.keys():
        anaID, datasetID = dataID.split(":")
        obs = data[dataID]["origN"]
        bg = data[dataID]["expectedBG"]
        bgerr = fudge*data[dataID]["bgError"]
        if bg == 0.: # bg needs to be greater than 0
            continue
        sigN = 0.

        d = { "id": anaID, "datasetId": datasetID, "bg": bg,
              "obs": obs, "bgerr": bgerr, "txns": data[dataID]["txns"] }
        if "sigN" in data[dataID]:
            hasWarned["signals"]+=1
            if hasWarned["signals"]<2:
                print ( f"[createData] there are signals in the database, we will subtract them from the observation!" )
            # signal mode, we remove the signal
            sigN = data[dataID]["sigN"]
            d["sigN"] = sigN
            d["obs"] = obs - sigN
        debug = True
        if debug:
            d["fudge"]=fudge
        from ptools.helpers import computeP
        p_norm = computeP ( obs - sigN, bg, bgerr, lognormal = False,
                            nmin = nmin, nmax = nmax )
        d["p_norm"]=p_norm
        p_lognorm = computeP ( obs - sigN, bg, bgerr, lognormal = True,
                            nmin = nmin, nmax = nmax )
        d["p_lognorm"] = p_lognorm
        ret.append ( d )
    return ret

def filterData( data : dict ) -> dict:
    """ here we just filter a bit, we dont need all fields, and
    we drop the upper limits """
    d = {}
    params = ["origN","expectedBG","bgError","orig_Z","new_Z","newObs","txns",\
              "sigN"]
    for dataID in data.keys():
        if ":ul:" in dataID:
            continue
        d[dataID] = {}
        for i in params:
            if i in data[dataID]:
                d[dataID][i] = data[dataID][i]
    return d

def writeHeader ( f ):
    """ write the header info into file handle f """
    import time, sys
    f.write ( f"# this file was created at {time.asctime()}\n" )
    args = ""
    for i in sys.argv:
        if " " in i or "," in i or "[" in i:
            i = f'"{i}"'
        args += f"{i} "
    f.write ( f"# via {args.strip()}\n" )
    f.write ( f"#\n" )
    f.write ( f"# variables:\n" )
    f.write ( f"# ==========\n" )
    f.write ( f"# obs: observed yield\n" )
    f.write ( f"# bg: background expectation, as a yield\n" )
    f.write ( f"# bgerr: error on background expectation\n" )
    f.write ( f"# p_norm: p-value for Gaussian nuisances\n" )
    f.write ( f"# p_lognorm: p-value for lognorm nuisances\n" )
    f.write ( "\n" )

def createData( dictfile : str, fudge_factors : list,
       nmin : int = 20000, nmax : int = 50000, outfile : str = "data.dict" ):
    """ create the data needed for the conservatism plots.
    :param dictfile: filename of _database.dict file to base this on
    :param nmin: minimum number of toys to throw for computation of pvalues
    :param nmax: maximum number of toys to throw for computation of pvalues
    :param outfile: dict file to store results in
    """
    # the most important parameters

    from multiverse.expResModifier import readDatabaseDictFile
    d = readDatabaseDictFile ( dictfile )

    header, data = d["meta"], d["data"]
    print ( f"[createData] {len(data)} signal regions will be considered" )

    d = filterData ( data )

    pvalues={}
    for fudge in fudge_factors:
        p = computePValues( d, fudge, nmin = nmin, nmax = nmax )
        pvalues[float(fudge)]=p

    from ptools.helpers import py_dumps
    print ( f"[createData] creating {outfile}" )
    with open ( outfile, "wt" ) as f:
        writeHeader ( f )
        ds = py_dumps ( pvalues ) # , stop_at_level = 2 )
        f.write ( ds+ "\n" )

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=
            "Produce the data for the conservatism plots")
    ap.add_argument('-d', '--dictfile',
            help='path to database dictionary file [../../protomodels/historic_database_stats/310.dict]',
            default='../../protomodels/historic_database_stats/310.dict')
    ap.add_argument('-o', '--outfile',
            help="output file, 'default' -> '<ntoys>.dict' ['data.dict']",
            default='data.dict')
    ap.add_argument('-f', '--ffactors',
            help='fudge factors, a list [None]', type=str,
            default=None)
    ap.add_argument('-n', '--nmin', type=int,
            help='minimum number of toys [50000]', default=50000)
    ap.add_argument('-N', '--nmax', type=int,
            help='maximum number of toys [100000]', default=100000)
    args = ap.parse_args()
    ffactors = args.ffactors
    if ffactors == None:
        ffactors = sorted(set([round(x,5) for x in (
            [i*0.05 for i in range(21)] +
            [0.3 + i*0.025 for i in range(int((0.65-0.3)/0.025)+1)] +
            [0.35 + i*0.0125 for i in range(int((0.55-0.35)/0.0125)+1)]
        )]))
        ffactors[0]=0.03
    if type(ffactors)==str:
        ffactors = eval(ffactors)
    if args.outfile == "default":
        args.outfile = f"{args.ntoys}.dict"
    createData( args.dictfile, ffactors, nmin = args.nmin, nmax = args.nmax, 
                outfile = args.outfile )

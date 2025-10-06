#!/usr/bin/env python3
# coding: utf-8

""" a script that creates the data for the conservatism plots """

import scipy.stats
import numpy as np

import sys
sys.path.insert(0,"../../protomodels/")

def computePValues( data : dict, fudge : float , ntoys : int ) -> dict:
    """ compute p-values 
    :param nuisanceType: gauss or lognorm
    """
    ret = []
    for dataID in data.keys():
        anaID, datasetID = dataID.split(":")
        obs = data[dataID]["origN"]
        bg = data[dataID]["expectedBG"]
        bgerr = fudge*data[dataID]["bgError"]
        if bg == 0.: # bg needs to be greater than 0
            continue

        ## first gauss
        central = bg
        lmbda = scipy.stats.norm.rvs ( loc=[central]*ntoys, scale=[bgerr]*ntoys )
        lmbda = lmbda[lmbda>0.]
        fakeobs = scipy.stats.poisson.rvs ( lmbda )

        p = float ( (sum(fakeobs>obs) + .5*sum(fakeobs==obs)) / len(fakeobs) )
        d = { "id": anaID, "datasetId": datasetID, "p_norm": p, "bg": bg }

        # then lognorm
        loc = central**2 / np.sqrt ( central**2 + bgerr**2 )
        stderr = float ( np.sqrt ( np.log ( 1 + bgerr**2 / central**2 ) ) )
        if stderr == 0.:
            d["p_lognorm"] = 0.
        else:
            lmbda = scipy.stats.lognorm.rvs ( s=[stderr]*ntoys, scale=[loc]*ntoys )
            fakeobs = scipy.stats.poisson.rvs ( lmbda )
            p = float ( (sum(fakeobs>obs) + .5*sum(fakeobs==obs)) / len(fakeobs))
            d [ "p_lognorm" ] = p
        ret.append ( d )
    return ret

def filterData( data : dict ) -> dict:
    """ here we just filter a bit, we dont need all fields, and 
    we drop the upper limits """
    d = {}
    params = ["origN","expectedBG","bgError","orig_Z","new_Z","newObs"]
    for dataID in data.keys():
        if ":ul:" in dataID:
            continue
        d[dataID] = {}
        for i in params:
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
    f.write ( f"# variables:" )
    f.write ( f"# ==========" )
    f.write ( f"# bg: background expectation, as a yield\n" )
    f.write ( f"# p_norm: p-value for Gaussian nuisances\n" )
    f.write ( f"# p_lognorm: p-value for lognorm nuisances\n" )
    f.write ( "\n" )

def createData( dictfile : str, fudge_factors : list,
       ntoys : int = 1000, outfile : str = "data.dict" ):
    """ create the data needed for the conservatism plots.
    :param dictfile: filename of _database.dict file to base this on
    :param ntoys: number of toys to throw for computation of pvalues
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
        p = computePValues( d, fudge, ntoys = ntoys)
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
            help='output file [data.dict]', 
            default='data.dict')
    ap.add_argument('-f', '--ffactors',
            help='fudge factors, a list [None]', type=str,
            default=None)
    ap.add_argument('-n', '--ntoys', type=int,
            help='number of toys [1000]', default=1000)
    args = ap.parse_args()
    ffactors = args.ffactors
    if ffactors == None:
        ffactors = sorted(set([round(x,5) for x in (
            [i*0.05 for i in range(21)] +
            [0.35 + i*0.025 for i in range(int((0.65-0.35)/0.025)+1)] +
            [0.45 + i*0.0125 for i in range(int((0.55-0.45)/0.0125)+1)]
        )]))
    if type(ffactors)==str:
        ffactors = eval(ffactors)
    createData( args.dictfile, ffactors, args.ntoys, args.outfile )

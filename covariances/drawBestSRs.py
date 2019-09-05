#!/usr/bin/env python3

""" simple plot of best signal region, should be turned into 
a full blown script """

import matplotlib.pyplot as plt
import copy
import numpy
import importlib

def convertNewAxes ( newa ):
    """ convert new types of axes (dictionary) to old (lists) """
    axes = copy.deepcopy(newa)
    if type(newa)==list:
        return axes[::-1]
    if type(newa)==dict:
        axes = [ newa["x"], newa["y"] ]
        if "z" in newa:
            axes.append ( newa["z"] )
        return axes[::-1]
    print ( "cannot convert this axis" )
    return None

def draw( validationfile ):
    anaId = "???"
    coll = "CMS"
    p = validationfile.find ( "ATLAS" )
    if p > 0:
        coll = "ATLAS"
    else:
        p = validationfile.find ( "CMS" )
    p2 = validationfile.find("-eff" )
    anaId = validationfile[p+1+len(coll):p2]
    spec = importlib.util.spec_from_file_location( "output", validationfile )
    output_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(output_module)
    validationData = output_module.validationData
    bestSRs = []
    nbsrs = []
    for point in validationData:
        if "error" in point:
            # print ( "skipping %s: %s" % ( point["slhafile"], point["error"] ) )
            continue
        axes = convertNewAxes ( point["axes"] )
        bestSRs.append ( ( axes[1], axes[0], point["dataset"] ) )
        nbsrs.append ( ( axes[1], axes[0], 0 ) )
    bestSRs.sort()
    nbsrs = numpy.array ( nbsrs )
    srDict, nrDict = {}, {}
    srNum = 0
    for ctr,x in enumerate(bestSRs):
        if x[2] not in srDict.keys():
            srDict[x[2]]=srNum
            nrDict[srNum]=x[2]
            srNum+=1
        nbsrs[ctr][0] = x[0]
        nbsrs[ctr][1] = x[1]
        nbsrs[ctr][2] = srDict[x[2]]
    #for x in nbsrs:
    #    print ( x )
    colors = ( "r", "g", "b", "c", "m", "y" )
    for n in nrDict.keys():
        x,y=[],[]
        for x_,y_,z_ in nbsrs:
            if n == int(z_):
                x.append ( x_ )
                y.append ( y_ )
        plt.scatter ( x, y, s=25, c=[colors[n]]*len(x), label=nrDict[n] )
    plt.legend( loc="upper right" )
    plt.xlabel ( "m$_{mother}$ [GeV]" )
    plt.ylabel ( "$\\Delta$m [GeV]" )
    plt.title ( "Best Signal Region, %s" % anaId )
    plt.savefig ( "bestSRs.png" )
    
if __name__ == "__main__":
    dbpath = "../../smodels-database/"
    anaId = "ATLAS-SUSY-2016-15"
    filename = "%s/13TeV/ATLAS/%s-eff/validation/T2ttoff_2EqMassAx_EqMassBy.py" % \
               ( dbpath, anaId )
    draw( filename )

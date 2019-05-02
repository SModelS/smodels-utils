#!/usr/bin/env python3

"""
.. module:: helpers
        :synopsis: little helper snippets for the bakery.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import numpy
import sys
sys.path.insert(0,"../../smodels" )
from smodels.tools.runtime import nCPUs

def dirName ( process, masses ):
    """ the name of the directory of one process + masses """
    return process + "." + "_".join(map(str,masses))

def parseMasses ( massstring, filterOrder=True ):
    """ parse the mass string, e.g. (500,510,10),(100,110,10). keywords like "half" are
        accepted.
    :param filterOrder: if true, discard vectors with daughters more massive than their
                           mothers.
    :returns: a list of all model points. E.g. [ (500,100),(510,100),(500,110),(510,110)].
    """
    try:
        masses = eval ( massstring )
    except NameError as e:
        masses = ""
    if type(masses) != tuple or len(masses)<2:
        mdefault = "(500,510,10),(100,110,10)"
        print ( "Error: masses need to be given as e.g. %s (you will need to put it under parentheses)" % mdefault )
        sys.exit()
    lists=[]
    for ctr,mtuple in enumerate(masses): ## tuple by tuple
        tmp=[]
        if type(mtuple) in [ str ]: ## descriptive strings
            if mtuple == "half" and ctr == 1:
                tmp.append ( mtuple )
                lists.append ( tuple(tmp) )
                continue
            else:
                print ( "error: i know only 'half' for a string, and only in middle position" )
                sys.exit()
        if type(mtuple) in [ int, float ]:
            tmp.append ( mtuple )
            lists.append ( tuple(tmp) )
            continue
        if len(mtuple) == 1:
            tmp.append ( mtuple[0] )
            continue
        if len(mtuple) == 2:
            mtuple = ( mtuple[0], mtuple[1], 10 )
        for i in numpy.arange(mtuple[0],mtuple[1],mtuple[2] ):
            tmp.append ( i )
        lists.append ( tuple(tmp) )
    # mesh = numpy.meshgrid ( *lists )
    if lists[1][0]=="half":
        ret = []
        for x  in lists[0]:
            for z in lists[2]:
                y=int(.5*x+.5*z)
                ret.append ( (x,y,z) )
        return ret
    ret = []
    if len(lists)==2:
        for x in range ( len(lists[0] ) ):
            for y in range ( len(lists[1]) ):
                if filterOrder and lists[1][y] > lists[0][x]:
                    continue
                ret.append ( (lists[0][x],lists[1][y]) )
    if len(lists)==3:
        for x in range ( len(lists[0] ) ):
            for y in range ( len(lists[1]) ):
                if filterOrder and lists[1][y] > lists[0][x]:
                    continue
                for z in range ( len(lists[2]) ):
                    if filterOrder and lists[2][z] > lists[1][y]:
                        continue
                    ret.append ( (lists[0][x],lists[1][y],lists[2][z]) )
    return ret

def nJobs ( nproc, npoints ):
    """ determine the number of jobs we should run, given nproc is
        the user's input for number of processes, and npoints is the number
        of points to be processed. """
    ret = nproc
    if ret < 1:
        ret = nCPUs() + ret
    if ret > npoints:
        ret = npoints
    return ret

def getListOfMasses(topo, njets, postMA5=False ):
    """ get a list of the masses of an mg5 scan. to be used for e.g. ma5.
    :param postMA5: query the ma5 output, not mg5 output.
    """
    import glob
    ret=[]
    fname = "%s_%djet.*" % ( topo, njets )
    if postMA5:
        fname="ma5/ANA_"+fname
    files = glob.glob( fname )
    for f in files:
        p=f.find("jet.")
        masses = tuple(map(int,map(float,f[p+4:].split("_"))))
        ret.append ( masses )
    return ret

def nRequiredMasses(topo):
    """ find out how many masses a topology requires """
    M=set()
    with open("slha/%s_template.slha" % topo, "r" ) as f:
        for line in f.readlines():
            if not "M" in line:
                continue
            p = line.find("M")
            num=line[p+1]
            if num not in list(map(str,range(6))):
                continue
            M.add(num)
    return len(M)

if __name__ == "__main__":
    # print ( getListOfMasses("T2",0) )
    #print ( parseMasses("500,100"))
    print ( nRequiredMasses("T5ZZ") )

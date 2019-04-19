#!/usr/bin/env python3

"""
.. module:: helpers
        :synopsis: little helper snippets for the bakery.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import numpy
from smodels.tools.runtime import nCPUs

def dirName ( process, masses ):
    """ the name of the directory of one process + masses """
    return process + "." + "_".join(map(str,masses))

def parseMasses ( massstring, filterOrder=False ):
    """ parse the mass string, e.g. (500,510,10),(100,110,10).
    :param filterOrder: if trrue, discard vectors with daughters more massive than their
     mothers.
    :returns: a list of all model points. E.g. [ (500,100),(510,100),(500,110),(510,110)].
    """
    try:
        masses = eval ( massstring )
    except NameError as e:
        masses = ""
    if type(masses) != tuple or len(masses)<2:
        print ( "Error: masses need to be given as e.g. %s (you will need to put it under parentheses)" % mdefault )
        sys.exit()
    lists=[]
    for mtuple in masses: ## tuple by tuple
        tmp=[]
        if type(mtuple) in [ int, float ]:
            tmp.append ( mtuple )
            continue
        if len(mtuple) == 1:
            tmp.append ( mtuple[0] )
            continue
        if len(mtuple) == 2:
            mtuple = ( mtuple[0], mtuple[1], 10 )
        for i in numpy.arange(mtuple[0],mtuple[1],mtuple[2] ):
            tmp.append ( i )
        lists.append ( tuple(tmp) )
    mesh = numpy.meshgrid ( *lists )
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

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
    """ the name of the directory of one process + masses 
    :param process: e.g. T2_1jet
    :param masses: tuple or list of masses, e.g. (1000, 800)
    """
    return process + "." + "_".join(map(str,masses))

def parseMasses ( massstring, mingap1=None, maxgap1=None,
                  mingap2=None, maxgap2=None, mingap13=None, maxgap13=None ):
    """ parse the mass string, e.g. (500,510,10),(100,110,10). keywords like "half" are
        accepted.
    :param mingap1: min mass gap between first and second particle, ignore if None.
                    this is meant to force onshellness or a mass hierarchy
    :param maxgap1: max mass gap between second and third particle, ignore if None.
                    this is meant to force offshellness
    :param mingap2: min mass gap between second and third particle, ignore if None.
                    this is meant to force onshellness or a mass hierarchy
    :param maxgap2: max mass gap between second and third particle, ignore if None.
                    this is meant to force offshellness
    :param mingap13: min mass gap between second and third particle, ignore if None.
                    this is meant to force onshellness or a mass hierarchy
    :param maxgap2: max mass gap between first and third particle, ignore if None.
                    this is meant to force offshellness
    :returns: a list of all model points. E.g. [ (500,100),(510,100),(500,110),(510,110)].
    """
    try:
        masses = eval ( massstring )
    except NameError as e:
        masses = ""
    if type(masses) not in [ list, tuple ] or len(masses)<2:
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
    ret = []
    if lists[1][0]=="half":
        for x  in lists[0]:
            for z in lists[2]:
                y=int(.5*x+.5*z)
                ret.append ( (int(x),y,int(z)) )
    elif len(lists)==2:
        for x in range ( len(lists[0] ) ):
            for y in range ( len(lists[1]) ):
                ret.append ( (int(lists[0][x]),int(lists[1][y])) )
    elif len(lists)==3:
        for x in range ( len(lists[0] ) ):
            for y in range ( len(lists[1]) ):
                for z in range ( len(lists[2]) ):
                    ret.append ( (int(lists[0][x]),int(lists[1][y]),int(lists[2][z])) )
    ret = filterForGap ( ret, mingap1, True, [0,1] )
    ret = filterForGap ( ret, mingap2, True, [1,2] )
    ret = filterForGap ( ret, mingap13, True, [0,2] )
    ret = filterForGap ( ret, maxgap1, False, [0,1] )
    ret = filterForGap ( ret, maxgap2, False, [1,2] )
    ret = filterForGap ( ret, maxgap13, True, [0,2] )
    return ret

def filterForGap ( masses, gap, isMin=True, indices=[0,1] ):
    """ filter out tuples for which gap is not met 
        between <indices> particles
    :param isMin: if True, filter out too low gaps, if False,
                  filter out too high gaps
    """
    if gap == None:
        return masses
    if len(masses[0])<=max(indices): ## not enough masses
        return masses
    ret = []
    for t in masses:
        if isMin and t[ indices[0] ] > t[ indices[1] ]+  gap:
            ret.append ( t )
        if not isMin and t[ indices[0] ] < t[ indices[1] ]+ gap:
            ret.append ( t )
    return ret

def ma5AnaNameToSModelSName ( name ):
    """ translate an analysis name from MA5 naming to
        SModelS naming (atlas -> ATLAS, etc) """
    name = name.replace("atlas","ATLAS")
    name = name.replace("cms","CMS")
    name = name.replace("susy","SUSY")
    name = name.replace("sus","SUS")
    name = name.replace("_","-")
    return name

def listAnalyses ( ):
    """ list the analyses that are available in MA5 """
    import glob
    # dname = "ma5/tools/PAD/Build/"
    dname = "ma5.template/tools/PAD/Build/SampleAnalyzer/User/Analyzer/"
    print ( "[bakeryHelpers] searching for analyses in %s" % dname )
    files = glob.glob ( "%s/*.cpp" % dname )
    # files = glob.glob ( "%s*.saf" % dname )
    print ( "List of analyses:" )
    for f in files:
        print  ( "  %s" % f.replace(".saf","").replace(dname,"").replace(".cpp","") )

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
    ms = "[(200,400,50.),(200,400.,50),(150.,440.,50)]"
    masses = parseMasses ( ms, mingap13=0., mingap2=0. )
    print ( "masses", masses )
    print ( nRequiredMasses("T5ZZ") )

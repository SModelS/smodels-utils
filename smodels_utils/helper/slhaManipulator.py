#!/usr/bin/python

"""
.. module:: slhaManipulator
        :synopsis: all sorts of manipulations of SLHA files.
                   FIXME we also want removal of dupes,
                   keeping the last entry.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from typing import Union, Dict

def getParticleIdsForTemplateFile ( filename : str ) -> Dict:
    """ given a template file name, return a dictionary of 
    pids, with positions as keys.

    :param filename: filename, e.g. T1.template
    :returns: dictionary, position as keys, pids as values.
    """
    import os
    def canonizeFilename ( filename : str ):
        from smodels_utils import SModelSUtils
        if not filename.endswith ( ".template" ):
            filename = f"{filename}.template"
        if not "/" in filename:
            filename = f"{SModelSUtils.installDirectory()}/slha/templates/{filename}"
        return filename
    path = canonizeFilename ( filename )
    filename = os.path.basename ( path )
    txname = filename.replace(".template","")
    f = open ( path, "rt" )
    lines = f.readlines()
    f.close()
    ret = {}
    pids, wpids = {}, {}
    for line in lines:
        p1 = line.find("#")
        if p1 > 0:
            line = line[:p1]
        for x in [ 0, 1, 2 ]:
            if f"M{x}" in line or f"m{x}" in line:
                tokens = line.split()
                if not x in pids:
                    pids[x]=set()
                pids[x].add ( int(tokens[0]) )
            if f"W{x}" in line or f"w{x}" in line:
                tokens = line.split()
                if not x in wpids:
                    wpids[x]=set()
                wpids[x].add ( int(tokens[1]) )
    return { "masses": pids, "widths": wpids }

def extractSLHAFileFromTarball ( slhafile, tarball=None, extractToDir=None ):
    """
    extract one specific slha file from a tarball
    :param tarball: if supplied, extract from that tarball,
                    if None, look for tarball in smodels-utils/slha/
    :param extractToDir: if supplied, extract into the given directory,
    else extract to cwd
    :returns: path to slhafile
    """
    if tarball == None:
        p1 = -1
        while slhafile[p1+1].isalpha():
            p1 = slhafile.find("_",p1+1)
        import os, tarfile
        from smodels_utils import SModelSUtils
        tarf = slhafile[:p1]+".tar.gz"
        tarball = os.path.join ( SModelSUtils.installDirectory(), "slha", tarf )
    if not os.path.exists ( tarball ): ## no tarball!
        print ( f"[slhaManipulator] tarball {tarball} does not exist!" )
        return None
    tar = tarfile.open ( tarball, "r:gz" )
    fobj = tar.extractfile ( slhafile )
    txt = fobj.read()
    targetfile = slhafile
    if extractToDir != None:
        targetfile = f"{extractToDir}/{slhafile}"
    with open ( targetfile, "wt" ) as f:
        f.write ( txt.decode("ascii") )
        f.close()
    tar.close()

    return targetfile

def removeXSecs ( In, Out=None ):
    """
    removes all XSECTION blocks
    :params In: name of input filename
    :params Out: name of output filename. If None, In is overwritten.
    :params In: name of input filename

    """
    f=open(In)
    lines=f.readlines()
    f.close()
    if Out==None: Out=In
    f=open(Out,"w")
    inXSecBlock=False
    for (ctr,line) in enumerate(lines):
        if not inXSecBlock and line.find("XSECTION")==-1:
            f.write(line)
        if line.find("XSECTION")>-1:
            inXSecBlock=True
            continue
        if inXSecBlock==True:
            tokens=line.split()
            if len(tokens)==0:
                continue
            if tokens[0].isalpha():
                inXSecBlock=False
            continue
    f.close()

def removeDupes ( In, Out=None ):
    """ removes multiple identical xsection entries,
        always keeping the first entry.
        :params In: name of input filename
        :params Out: name of output filename. If None, In is overwritten.

    """
    f=open(In)
    lines=f.readlines()
    f.close()
    if Out==None: Out=In
    f=open(Out,"w")

    xsecLines=[]

    isInXSecBlock=False
    skipNextLine=False
    for line in lines:
        if skipNextLine: ## are we in a second line of an xsec record?
            skipNextLine=False ## skip it!
            continue
        if line.find ("XSECTION")==0:
            isInXSecBlock=True # in xsec block?
            if line in xsecLines: ## do we have the line stored already?
                skipNextLine=True ## then skip this line and the next
                continue
        if not isInXSecBlock: ## not in xsec section? copy the lines!
            f.write ( line )
            continue
        ## we are in xsec block, and the line doesnt yet exist?
        ## write it! and remember it!
        f.write ( line )
        xsecLines.append ( line )

    f.close()

if __name__ == '__main__':
    import sys
    t=sys.argv[1:]
    if len(t)==0:
        t.append("test.slha")
    for i in t:
        ## removeDupes( i )
        removeXSecs( i )


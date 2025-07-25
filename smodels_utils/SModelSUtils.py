#!/usr/bin/env python3

"""
.. module:: SModelSUtils
    :synopsis: SModelSUtils entry point.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

def installDirectory():
    """ return the software installation directory, by looking at location of this method """
    import os
    import inspect
    ret=os.path.realpath ( inspect.getabsfile(installDirectory) )
    ret=ret.replace("SModelSUtils.py","")
    ret=ret.replace("smodels_utils/","")
    return ret

def addInstallDirectory():
    """ add this directory to search path """
    import sys, os
    iDir = installDirectory()
    if os.path.isdir ( iDir ):
        sys.path.append ( iDir )
    return iDir

def version(astuple=False):
    """
    Print version number of smodels-utils

    """
    f = open(f"{installDirectory()}/version")
    l = f.readline()
    f.close()
    l = l.replace("\n", "")
    l.strip()
    if not astuple:
        return l
    a, b = l.split(".")
    return (int(a), int(b))

def addSModelSPath():
    """ adds the path of where smodels is installed to the search  path """

    #First try home/smodels. If it doesn't exist, look for other locations
    import os,sys
    home = os.path.expanduser("~")
    smodelsDir = os.path.join(home,'smodels')
    if os.path.isdir(smodelsDir):
        sys.path.append(smodelsDir)
        return smodelsDir
    smodelsDir = os.path.join(home,'git','smodels')
    if os.path.isdir(smodelsDir):
        sys.path.append(smodelsDir)
        return smodelsDir
            
    try:
        from smodels import SModelS
        # I=SModelS.installDirectory()
        J=SModelS.pythonDirectory()
        import sys
        # sys.path.append ( I )
        if os.path.isdir ( J ):
            sys.path.append ( J )
        return J
    except ImportError as e:
        pass
    try:
        import subprocess as commands
    except:
        import commands
    O=commands.getoutput("smodels-config --pythondir")
    if O.find("not found")==-1:
        import sys
        sys.path.append(O)
        return O
    return ""

def printHelp():
    print ("usage: smodels-utils-config [--help] [--installdir] [--smodelsdir]")
    print ("")
    print ("optional arguments:")
    print ("  --help          show this help message and exit")
    print ("  --installdir    print installation directory of smodels-utils")
    print ("  --smodelsdir    print installation directory of smodels")
    import sys
    sys.exit(0)

if __name__ == "__main__":
    import sys
    if len(sys.argv)<2: printHelp()
    for i in sys.argv[1:]:
        if i=="--help": printHelp()
        if i=="--installdir":
            print ( installDirectory() )
            sys.exit(0)
        if i=="--smodelsdir":
            print ( addSModelSPath() )
            sys.exit(0)
    printHelp()


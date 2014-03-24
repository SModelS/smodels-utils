#!/usr/bin/env python

"""
.. module:: SModelSTools
    :synopsis: SModelSTools entry point.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def installDirectory():
    """ return the software installation directory, by looking at location of this method """
    import os, inspect
    ret=os.path.realpath ( inspect.getabsfile(installDirectory) )
    ret=ret.replace("SModelSTools.py","")
    return ret

def addInstallDirectory():
    """ add this directory to search path """
    import sys, inspect, os
    base=os.path.dirname ( os.path.realpath ( inspect.getabsfile(addInstallDirectory) ) )
    sys.path.append ( base )

def addSModelSPath():
    """ adds the path of where smodels is installed to the search  path """
    try:
        import SModelS
        I=SModelS.installDirectory()
        import sys
        sys.path.append ( I )
        return
    except ImportError,e:
        pass
    import commands
    O=commands.getoutput("smodels-config --installdir")
    if O.find("not found")==-1:
      import sys
      sys.path.append(O)
      return O
    return ""

def printHelp():
    print "usage: smodels-tools-config [--help] [--installdir] [--smodelsdir]"
    print ""
    print "optional arguments:"
    print "  --help          show this help message and exit"
    print "  --installdir    print installation directory of smodels-tools"
    print "  --smodelsdir    print installation directory of smodels"
    import sys
    sys.exit(0)

if __name__ == "__main__":
    import sys
    if len(sys.argv)<2: printHelp()
    for i in sys.argv[1:]:
        if i=="--help": printHelp()
        if i=="--installdir": 
            print installDirectory()
            sys.exit(0)
        if i=="--smodelsdir": 
            print addSModelSPath()
            sys.exit(0)
    printHelp()


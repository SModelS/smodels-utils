#!/usr/bin/env python

"""
.. module:: setPath
   :synopsis: Sets the path such that e.g. from smodels.tools import toolBox works.
              correctly. Called as a script, the path is printed.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def configure():
    """ get the path name of this file, remove setPath.py, 
        remove the last subdir, the remaining string should be the
        base path name """
    import os, inspect, sys
    ret=os.path.realpath ( inspect.getabsfile(configure) )
    ret=ret.replace("/bin/setPath.py","")
    sys.path.append ( ret )
    ret= "../"
    sys.path.append ( ret )
    from smodels_utils import SModelSUtils
    r= ( SModelSUtils.addInstallDirectory(), )
    r+= ( SModelSUtils.addSModelSPath(), )
    for x in r:
        sys.path.append ( x )
    return r

configure()

if __name__ == "__main__":
    """
    Called as a script, print out the path.

    """
    print(f"The following strings are appended to the path variable: {configure()!s}" )

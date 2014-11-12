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
    import sys
    r=()
    ret= "../"
    sys.path.append ( ret )
    r+=(ret,)
    from smodels_tools import SModelSTools
    
    r+= ( SModelSTools.addInstallDirectory(), )
    r+= ( SModelSTools.addSModelSPath(), )
    return r

configure()

if __name__ == "__main__":
    """
    Called as a script, print out the path.

    """
    print("The following strings are appended to the path variable:",
          configure())

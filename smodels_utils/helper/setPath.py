#!/usr/bin/env python

""" this sets the path so we can write e.g. "from smodels_utils.tools import blah """

def configure():
    """ get the path name of this file, remove setPath.py, 
        remove the last subdir, the remaining string should be the
        base path name """
    import sys
    ret="../../"
    sys.path.append ( ret )
    from smodels_utils import SModelSUtils
    SModelSUtils.addInstallDirectory()
    SModelSUtils.addSModelSPath()
    return ret
    

configure()

if __name__ == "__main__":
    print ( configure() )

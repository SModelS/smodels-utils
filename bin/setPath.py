""" this sets the path so we can write e.g. "from smodels_tools.tools import blah """

def configure():
    """ get the path name of this file, remove setPath.py, 
        remove the last subdir, the remaining string should be the
        base path name """
    import sys
    sys.path.append ( "../" )
    import SModelSTools
    SModelSTools.addInstallDirectory()
    SModelSTools.addSModelSPath()

configure()

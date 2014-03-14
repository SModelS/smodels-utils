""" this sets the path so we can write e.g. "from theory import blahblah """

def addSModelSPath():
    try:
        import SModelS
        I=SModelS.installdir()
        sys.path.append ( I )
        return
    except ImportError,e:
        pass
    import commands
    O=commands.getoutput("smodels-config --installdir")
    if O.find("not found")==-1:
      import sys
      print "O=",O
      sys.path.append(O)


def configure():
    """ get the path name of this file, remove set_path.py, 
        remove the last subdir, the remaining string should be the
        base path name """
    import sys, inspect, os
    base=os.path.dirname ( os.path.realpath ( inspect.getabsfile(configure) ) )
    pos=base.rfind("/")
    base=base[:pos+1]
    print "[set_path.py] appending",base
    sys.path.append ( base )
    addSModelSPath()

configure()

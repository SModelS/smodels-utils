#!/usr/bin/env python3

""" Simple script that handles the installation of MadGraph5.
FIXME not finished yet. """

import subprocess, os, sys
    
ver="2_6_5"

def install():
    if os.path.exists ( "bin/mg5_aMC" ):
        ## seems like we have an install
        return
    verdot = ver.replace("_",".")
    url="http://smodels.hephy.at/downloads/tarballs/"
    tarball = "MG5_aMC_v%s.tar.gz" % verdot
    if not os.path.exists ( tarball ):
        cmd = "wget %s/%s" % ( url, tarball )
        subprocess.getoutput ( cmd )
    cmd = "tar xzvf %s" % tarball
    subprocess.getoutput ( cmd )
    cmd = "mv MG5_aMC_v%s/* ."  % ver
    subprocess.getoutput ( cmd )
    if not os.path.exists ( "bin/mg5_aMC" ):
        print ( "something went wrong with the install. please check manually" )
        sys.exit()

def clean():
    import glob
    for file in glob.glob ( "*" ):
        if file not in [ "install.py", "install.txt" ]:
            cmd = "rm -rf %s" % file
            subprocess.getoutput ( cmd )

if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1]=="clean":
        clean()
    else:
        install()

#!/usr/bin/env python3

""" Simple script that handles the installation of MadGraph5.
FIXME not finished yet. """

import subprocess, os
    
ver="2_6_5"

def install():
    verdot = ver.replace("_",".")
    url="http://smodels.hephy.at/downloads/tarballs/"
    tarball = "MG5_aMC_v%s.tar.gz" % verdot
    if not os.path.exists ( tarball ):
        cmd = "wget %s/%s" % ( url, tarball )
        subprocess.getoutput ( cmd )

def clean():
    verdot = ver.replace("_",".")
    tarball = "MG5_aMC_v%s.tar.gz" % verdot
    if os.path.exists( tarball ):
        os.unlink ( tarball )

if __name__ == "__main__":
    install()

#!/usr/bin/env python3

""" Simple script that handles the installation of MadGraph5,
    and its plugins.
"""

import subprocess, os, sys
    
ver="2_6_5"

def install_plugins():
    print ( "installing plugins (tail -f /tmp/mg5.install to monitor) ... " )
    f=open("install.script","r")
    lines=f.readlines()
    f.close()
    for line in lines:
        if line[0]=="#":
            continue
        print ( " - %s" % line.strip() )
        f=open("install.txt","w")
        f.write(line)
        f.close()
        cmd = "bin/mg5_aMC -f install.txt 2>&1 | tee /tmp/mg5.install"
        subprocess.getoutput ( cmd )
    os.unlink ( "install.txt" )

def install():
    if os.path.exists ( "bin/mg5_aMC" ):
        ## seems like we have an install
        if not os.path.exists ( "HEPTools" ):
            install_plugins()
        return
    print ( "installing mg5 ..." )
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
    cmd = "rmdir MG5_aMC_v%s" % ver
    subprocess.getoutput ( cmd )
    if not os.path.exists ( "bin/mg5_aMC" ):
        print ( "something went wrong with the install. please check manually" )
        sys.exit()
    install_plugins()

def clean():
    import glob
    for file in glob.glob ( "*" ):
        if file not in [ "install.py", "install.script" ]:
            cmd = "rm -rf %s" % file
            subprocess.getoutput ( cmd )

if __name__ == "__main__":
    import inspect
    D = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) 
    os.chdir ( D )
    if len(sys.argv)>1 and sys.argv[1]=="clean":
        clean()
    else:
        install()

#!/usr/bin/env python3

""" Simple script that handles the installation of MadAnalysis5.
    and its plugins.
"""

import subprocess, os, sys
    
ver="1.7"

def install_plugins():
    print ( "installing plugins (tail -f /tmp/ma5.install to monitor) ... " )
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
        cmd = "python2 bin/ma5 -s -f install.txt 2>&1 | tee /tmp/ma5.install"
        a = subprocess.getoutput ( cmd )
        print ( a )
    os.unlink ( "install.txt" )

def install():
    if os.path.exists ( "bin/ma5" ):
        return
    print ( "installing ma5 ..." )
    url="http://smodels.hephy.at/downloads/tarballs/"
    tarball = "ma5_v%s.tgz" % ver
    if not os.path.exists ( tarball ):
        cmd = "wget %s/%s" % ( url, tarball )
        subprocess.getoutput ( cmd )
    cmd = "tar xzvf %s" % tarball
    subprocess.getoutput ( cmd )
    cmd = "mv madanalysis5/* ."
    subprocess.getoutput ( cmd )
    cmd = "rmdir madanalysis5"
    subprocess.getoutput ( cmd )
    cmd = "rm %s" % tarball
    subprocess.getoutput ( cmd )
    if not os.path.exists ( "bin/ma5" ):
        print ( "something went wrong with the install. please check manually" )
        sys.exit()
    install_plugins()

def clean():
    import glob
    for file in glob.glob ( "*" ):
        if file not in [ "make.py", "install.script", "Makefile" ]:
            cmd = "rm -rf %s" % file
            subprocess.getoutput ( cmd )

if __name__ == "__main__":
    import inspect
    D = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) 
    os.chdir ( D )
    if len(sys.argv)>1 and sys.argv[1]=="clean":
        clean()
        sys.exit()
    if len(sys.argv)>1 and sys.argv[1]=="plugins":
        install_plugins()
        sys.exit()
    install()

#!/usr/bin/env python3

""" Simple script that handles the installation of MadGraph5,
    and its plugins.
"""

import subprocess, os, sys
    
def install_plugins( pyver=2 ):
    ## use modified installer script
    ## modifyBoostInstaller()
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
        cmd = "python%d bin/mg5_aMC -f install.txt 2>&1 | tee /tmp/mg5.install" % pyver
        subprocess.getoutput ( cmd )
    if os.path.exists ( "install.txt" ):
        os.unlink ( "install.txt" )

def install( ver, plugins = True, pyver = 2 ):
    """
    :param ver: MG5 version (eg 2_7_2)
    :param plugins: install also plugins
    :param pyver: python version, 2 or 3
    """
    if os.path.exists ( "bin/mg5_aMC" ):
        ## seems like we have an install
        if not os.path.exists ( "HEPTools" ):
            install_plugins( pyver )
        else:
            print ( "[make.py] everything seems to be installed. Remove HEPTools or bin/mg5_aMC if you wish to trigger a reinstall" )
        return
    print ( "installing mg5 ..." )
    verdot = ver.replace("_",".")
    url="https://smodels.github.io/downloads/tarballs/"
    tarball = "MG5_aMC_v%s.tar.gz" % verdot
    if pyver == 3:
        tarball = "MG5_aMC_v%s.py3.tar.gz" % verdot
    if not os.path.exists ( tarball ):
        cmd = "wget %s/%s" % ( url, tarball )
        a = subprocess.getoutput ( cmd )
        if not os.path.exists ( tarball ):
            print ( "download failed: %s" % a )
            sys.exit()
    cmd = "tar xzvf %s" % tarball
    subprocess.getoutput ( cmd )
    cmd = "mv MG5_aMC_v%s/* ."  % ver
    if pyver == 3:
        cmd = "mv MG5_aMC_v%s_py3/* ." % ver
    subprocess.getoutput ( cmd )
    cmd = "rmdir MG5_aMC_v%s" % ver
    if pyver == 3:
        cmd += "_py3"
        # cmd = "rmdir MG5_aMC_v%s_py3" % ver
    subprocess.getoutput ( cmd )
    if not os.path.exists ( "bin/mg5_aMC" ):
        print ( "something went wrong with the install. please check manually" )
        sys.exit()
    if plugins:
        install_plugins( pyver )

def modifyBoostInstaller():
    ## seems to get overwritten again
    boostscript = "HEPTools/HEPToolsInstallers/installBOOST.sh"
    if not os.path.exists ( boostscript ):
        return
    f=open(boostscript,"r")
    lines=f.readlines()
    f.close()
    f=open("/tmp/boostinstaller","w")
    for line in lines:
        f.write ( line.replace("b2 install", "b2 -j`nproc` install" ) )
    f.close()
    cmd = "cp /tmp/boostinstaller %s" % boostscript
    a=subprocess.getoutput ( cmd )
    cmd = "chmod 500 %s" % boostscript
    a2=subprocess.getoutput ( cmd )
    print ( "cmd", cmd, a, a2, os.getcwd() )

def clean():
    print ( "cleaning up ... " )
    import glob
    for f in glob.glob ( "*" ):
        if f not in [ "make.py", "install.script", "Makefile" ]:
            cmd = "rm -rf %s" % f
            subprocess.getoutput ( cmd )

if __name__ == "__main__":
    import inspect
    D = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) 
    os.chdir ( D )
    import argparse
    argparser = argparse.ArgumentParser(
                  description='a utility script to help build MG5' )
    argparser.add_argument ( '--clean', help='clean all cruft files', action="store_true" )
    argparser.add_argument ( '--plugins', help='build the plugins', action="store_true" )
    argparser.add_argument ( '--noplugins', help='dont build the plugins, only the binary', 
                             action="store_true" )
    argparser.add_argument ( '-p', '--pyver', help='python version [2]',
                             type=int, default=2 )
    argparser.add_argument ( '-V', '--version', help='MG5 version [2_7_2]',
                             type=str, default="2_7_2" )
    args = argparser.parse_args()
    args.version = args.version.replace(".","_")
    if args.clean:
        clean()
        sys.exit()
    if args.plugins:
        install_plugins( args.pyver )
        sys.exit()
    plugins = True
    if args.noplugins:
        plugins = False 
    install( args.version, plugins=plugins, pyver= args.pyver )

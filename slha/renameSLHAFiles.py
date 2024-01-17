#!/usr/bin/env python3

""" very simple tool to rename the slha files produced with monoXSMS/madgraph
to something we can make use of """

import os, glob, tempfile, pyslha, shutil, subprocess
from typing import Dict

def renameSLHAFile( filename : os.PathLike, prefix : str, pids : Dict ):
    """ rename a single slha file 

    :param path: a directory in which we search for slha files
    :param prefix: prefix for slha file names and final tarball name e.g. TRV1jj
    :param pids: dictionary with particle ids
    :returns: filename
    """
    f = pyslha.readSLHAFile ( filename )
    pmasses = f.blocks["MASS"]
    masses = {}
    for var,pid in pids.items():
        if pid in pmasses:
            masses[var]=pmasses[pid]
        else:
            masses[var]=None
    newfilename = f"{prefix}_{int(masses['x'])}"
    #newfilename = f"{prefix}_{masses['x']}"
    newfilename += ".slha"

    newfilepath = os.path.join ( prefix, newfilename )
    print ( filename, masses, newfilepath )
    shutil.move ( filename, newfilepath )
    return newfilename

def createTarball ( prefix : str ):
    """ given subfolder <prefix> create tarball """
    cmd = f"cd {prefix}; tar czvf ../{prefix}.tar.gz *.slha"
    # subprocess.getoutput ( cmd )

def renameSLHAFiles( path : os.PathLike, prefix : str,
       pids : Dict = { "x": 5000521, "y": 5000001 } ):
    """ rename the files found in path

    :param path: a directory in which we search for slha files
    :param prefix: prefix for slha file names and final tarball name e.g. TRV1jj
    :param pids: dictionary with particle ids
    :returns: path to final tarball
    """
    if os.path.exists ( prefix ):
        cmd = f"rm -rf {prefix}"
        subprocess.getoutput ( cmd )
    os.mkdir ( prefix )
    files = glob.glob ( os.path.join ( path, "*.slha" ) )
    for f in files:
        renameSLHAFile ( f, prefix, pids )
    createTarball ( prefix )
    shutil.rmtree ( prefix )

def untar ( tarball : os.PathLike ):
    """ untar the tarball """
    cmd = f"tar xzvf {tarball}"
    subprocess.getoutput ( cmd )

if __name__ == "__main__":
    # d = { "x": 5000521, "y": 5000001 } 
    d = { "x": 5000001 }
    untar ( "slhaFiles_Simp_Axial_Vector.tar.gz" )
    renameSLHAFiles( "slhaFiles_Simp_Axial_Vector", "TRV1jj", d )

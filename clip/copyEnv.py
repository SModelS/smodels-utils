#!/usr/bin/env python3

import subprocess, os, glob

def copy():
    files = [ ".bashrc", ".bash.aliases", ".vimrc", ".tmux.conf", ".vim/ftplugin", ".vim/syntax", ".gitconfig" ]
    for f in files:
        source = "/users/wolfgan.waltenberger/"
        dest = "/scratch-cbe/users/wolfgan.waltenberger/"
        if os.path.exists ( f"{dest}{f}" ):
            continue
        cmd = f"cp -rf {source}{f} {dest}{f}"
        subprocess.getoutput ( cmd )

def copySSH():
    files = glob.glob ( ".ssh/*" )
    for f in files:
        source = "/users/wolfgan.waltenberger/"
        dest = "/scratch-cbe/users/wolfgan.waltenberger/"
        if os.path.exists ( f"{dest}{f}" ):
            continue
        cmd = f"cp -rf {source}{f} {dest}{f}"
        subprocess.getoutput ( cmd )

def copyContainers():
    destdir = "/scratch-cbe/users/wolfgan.waltenberger/container/"
    sourcedir = "/mnt/hephy/pheno/"
    simg = "ubuntu2104sing38a.simg"
    if not os.path.exists ( destdir ):
        cmd = f"mkdir {destdir}" 
        subprocess.getoutput ( cmd )
    if not os.path.exists ( f"{destdir}{simg}" ):
        cmd = f"cp {sourcedir}{simg} {destdir}"
        # print ( cmd )
        subprocess.getoutput ( cmd )
    else:
        # print ( f"found container at {destdir}{simg}" )
        pass
    if not os.path.exists ( f"{destdir}current.simg" ):
        cmd = f"ln -s {destdir}{simg} {destdir}current.simg"
        subprocess.getoutput ( cmd )

if __name__ == "__main__":
    copy()
    copySSH()
    copyContainers()

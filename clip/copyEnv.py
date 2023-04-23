#!/usr/bin/env python3

import subprocess, os, glob, sys

def copy():
    files = [ ".bashrc", ".bash.aliases", ".vim", ".vimrc", ".tmux.conf", ".vim/ftplugin", ".vim/syntax", ".gitconfig", ".vim/colors", ".vim/colors/trinos.vim", ".local/bin/" ]
    for f in files:
        source = "/users/wolfgan.waltenberger/"
        dest = "/scratch-cbe/users/wolfgan.waltenberger/"
        if os.path.exists ( f"{dest}{f}" ):
            continue
        cmd = f"cp -rf {source}{f} {dest}{f}"
        subprocess.getoutput ( cmd )

def gitClone():
    Dir = "/scratch-cbe/users/wolfgan.waltenberger/git/"
    for i in [ "smodels", "smodels-utils", "smodels-database", "em-creator", "smodels.github.io", "protomodels" ]:
        if not os.path.exists ( f"{Dir}/{i}" ):
            cmd = f"cd {Dir}; git clone git+ssh://git@github.com/SModelS/{i}.git"
            print ( cmd )
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

def mkTempDir():
    destdir = "/scratch-cbe/users/wolfgan.waltenberger/tmp/"
    if not os.path.exists ( destdir ):
        cmd = f"mkdir {destdir}"
        subprocess.getoutput ( cmd )

def copyContainers():
    destdir = "/scratch-cbe/users/wolfgan.waltenberger/container/"
    sourcedir = "/groups/hephy/pheno/ww/containers/"
    simg = "ubuntu2210sing310a.simg"
    # simg = "ubuntu2204sing38b.simg"
    if not os.path.exists ( destdir ):
        cmd = f"mkdir {destdir}" 
        subprocess.getoutput ( cmd )
    if not os.path.exists ( f"{destdir}{simg}" ):
        cmd = f"cp {sourcedir}{simg} {destdir}"
        # print ( cmd )
        subprocess.getoutput ( cmd )
        if os.path.exists ( f"{destdir}current.simg" ):
            ## symlink needs resetting
            cmd = f"rm {destdir}current.simg"
            subprocess.getoutput ( cmd )
    else:
        # print ( f"found container at {destdir}{simg}" )
        pass
    if not os.path.exists ( f"{destdir}current.simg" ):
        cmd = f"ln -s {destdir}{simg} {destdir}current.simg"
        subprocess.getoutput ( cmd )

def storeDirectory():
    """ if current directory is not home, then make sure we 
        end up in it also within the container """
    cwd = os.getcwd()
    home= os.environ["HOME"]
    #cmd = f"cp {home}/.containerrc {home}/.tempcontainerrc"
    #subprocess.getoutput ( cmd )
    if cwd == home:
        return
    cmd = f"echo 'cd {cwd}' >> {home}/.cd_rc"
    subprocess.getoutput ( cmd )

if __name__ == "__main__":
    copy()
    copySSH()
    copyContainers()
    gitClone()
    mkTempDir()
    storeDirectory()

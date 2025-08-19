#!/usr/bin/env python3

""" A script that splits up the results into official and fastlim.
    (maybe later even more packages ) """

import os
import subprocess
import sys
sys.path.insert(0,"." )

from createTarballs import clearGlobalInfos

fastlimdir = "../../smodels-fastlim"
supersededdir = "../../smodels-superseded"

def run ( cmd, dryrun=False ):
    if dryrun:
        print ( f"Dry-run: skipping {cmd}." )
    else:
        print ( f"[moveFastlimResults] Executing: {cmd}." )
        subprocess.getoutput ( cmd )

def backupScript():
    ## first we copy ourself to /tmp
    cmd="cp ./moveFastlimResults.py /tmp/"
    subprocess.getoutput ( cmd )

def rmDirs():
    if os.path.exists ( fastlimdir ):
        cmd = f"rm -r {fastlimdir}"
        run ( cmd )

def mkDirs():
    cmd= f"mkdir {fastlimdir}"
    run ( cmd )

def moveFastlimResult ( path, dryrun ):
    """ <path> is a fastlim result -- move it to separate directory
    <fastlimdir> """
    dname = os.path.dirname ( path )
    bname = os.path.basename ( path )
    print ( f"{bname} is fastlim!" )
    if not os.path.exists ( f"{fastlimdir}/{dname}" ):
        cmd = f"mkdir -p {fastlimdir}/{dname}"
        run ( cmd )
    cmd = f"mv {path} {fastlimdir}/{dname}"
    if dryrun:
        cmd = f"cp -a {path} {fastlimdir}/{dname}"
    run ( cmd )
    cmd = f"rm -r {fastlimdir}/{path}/*/orig"
    run ( cmd )
    cmd = f"rm -r {fastlimdir}/{path}/*/convert.py"
    run ( cmd )
    cmd = f"rm -r {fastlimdir}/{path}/validation"
    run ( cmd )
    cmd = f"rm -r {fastlimdir}/{path}/sms.root"
    run ( cmd )

def moveSupersededResult ( path, dryrun ):
    """ <path> is a superseded result -- move it to separate directory
    <supersededdir> """
    dname = os.path.dirname ( path )
    bname = os.path.basename ( path )
    print ( f"{bname} is superseded!" )
    if not os.path.exists ( f"{supersededdir}/{dname}" ):
        cmd = f"mkdir -p {supersededdir}/{dname}"
        run ( cmd )
    cmd = f"mv {path} {supersededdir}/{dname}"
    if dryrun:
        cmd = f"cp -a {path} {supersededdir}/{dname}"
    run ( cmd )
    cmd = f"rm -r {supersededdir}/{path}/*/orig"
    run ( cmd )
    cmd = f"rm -r {supersededdir}/{path}/*/convert.py"
    run ( cmd )
    cmd = f"rm -r {supersededdir}/{path}/validation"
    run ( cmd )
    cmd = f"rm -r {supersededdir}/{path}/sms.root"
    run ( cmd )
    cmd = f"rm -r {supersededdir}/{path}/exclusion_lines.json"
    run ( cmd )

def createFastlimTarball():
    cmd = f"cd {fastlimdir}; tar czvf ../smodels-fastlim.tgz ./"
    run ( cmd )

def createSupersededTarball():
    cmd = f"cd {supersededdir}; tar czvf ../smodels-superseded.tgz ./"
    run ( cmd )

def traverse( dryrun ):
    """ now traverse the directories in the database """
    for i in os.listdir("."):
        if not os.path.isdir ( i ) or i in [ ".git" ]:
            continue
        for j in os.listdir ( i ):
            fulldir = os.path.join ( i, j )
            if not os.path.isdir ( fulldir ):
                continue
            superseded = set()
            for analysis in os.listdir ( fulldir ):
                fullpath = os.path.join ( fulldir, analysis )
                gi = f"{fullpath}/globalInfo.txt"
                gif=open ( gi )
                lines=gif.readlines()
                for line in lines:
                    if "supersedes" in line:
                        ss = line.replace("supersedes:","")
                        ss.strip()
                        superseded.add ( ss )
                gif.close()

            for analysis in os.listdir ( fulldir ):
                fullpath = os.path.join ( fulldir, analysis )
                gi = f"{fullpath}/globalInfo.txt"
                if not os.path.exists ( gi ):
                    continue
                gif=open ( gi )
                lines=gif.readlines()
                anaId = None
                for line in lines:
                    if "id" in line:
                        anaId = line.replace("id:","").strip()
                    if "fastlim" in line and "contact" in line:
                        moveFastlimResult ( fullpath, dryrun )
                        break
                    if "supersededBy" in line or anaId in superseded:
                        moveSupersededResult ( fullpath, dryrun )
                        break
                gif.close()
    clearGlobalInfos ( fastlimdir )

def error ( text ):
    print ( f"ERROR: {text}" )

def moveBibFile ( dryrun ):
    """ move fastlim-specific / superseded-specific bibliography file """
    fastlim_bib = "references-fastlim.bib"
    if not os.path.exists ( fastlim_bib ):
        error ( f"{fastlim_bib} is missing!" )
    else:
        cmd = f"mv {fastlim_bib} {fastlimdir}"
        run ( cmd, dryrun )
    superseded_bib = "references-superseded.bib"
    if not os.path.exists ( superseded_bib ):
        error ( f"{superseded_bib} is missing!" )
    else:
        cmd = f"mv {superseded_bib} {supersededdir}"
        run ( cmd, dryrun )
        
def moveReadmeFile ( dryrun ):
    """ move fastlim-specific / superseded-specific README file """
    fastlim_readme = "README_fastlim"
    if not os.path.exists ( fastlim_readme ):
        error ( f"{fastlim_readme} is missing!" )
    else:
        cmd = f"mv {fastlim_readme} {os.path.join(fastlimdir,'README' )}"
        run ( cmd, dryrun )        
    superseded_readme = "README_superseded"
    if not os.path.exists ( superseded_readme ):
        error ( f"{superseded_readme} is missing!" )
    else:
        cmd = f"mv {superseded_readme} {os.path.join(supersededdir,'README' )}"
        run ( cmd, dryrun )        

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument( '-d', '--dryrun',
            help='Dry-run, dont actuall move or create anything',
            action='store_true')
    #ap.add_argument( '-D', '--database', type=str,
    #        help='Path to database [database/smodels-database]',
    #        default='database/smodels-database')
    args = ap.parse_args()
    backupScript()
    rmDirs()
    mkDirs()
    traverse( args.dryrun )
    moveBibFile ( args.dryrun )
    moveReadmeFile ( args.dryrun )
    createFastlimTarball()
    createSupersededTarball()

if __name__ == "__main__":
    main()

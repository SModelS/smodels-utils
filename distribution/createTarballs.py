#!/usr/bin/env python3

"""
.. module:: createTarballs
   :synopsis: Script that is meant to create the distribution tarballs

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys, subprocess, os, time, argparse, glob, shutil 
from distributionHelpers import clearJsons, comment, runCmd, cloneDatabase, \
         clearGlobalInfos, createDatabase, removeNonValidated, moveNonAggregated
from smodels.experiment.databaseObj import Database
from typing import Union
sys.path.insert(0,"../")

dummyRun=False ## True

def isDummy( ):
    if dummyRun:
        comment( "DUMMY RUN!!!!" )
    return dummyRun

def rmlog(dirname):
    """ clear the log file """
    cmd="rm -f /tmp/create.log"
    if os.path.isfile('create.log'):
        os.remove('create.log')
    if os.path.isfile( f'{dirname}/smodels-database/create.log' ):
        os.remove( f'{dirname}/smodels-database/create.log' )

def mkdir(dirname):
    """
    Create a temporary directory for creating the tarball.
    """
    ## for i in( dirname, fastlimdir ):
    for i in( [ dirname ] ): ## , fastlimdir ):
        comment( f"Creating temporary directory {i}" )
        runCmd( f"mkdir -p {i}" )

def rmdir(dirname):
    """
    Remove the temporary directories
    """
    for i in( dirname, ): ## fastlimdir ):
        if os.path.exists(i):
            comment( f"Removing temporary directory {i}" )
            runCmd( f"rm -rf {i}" )

def makeClean(dirname):
    """
    Execute 'make clean' in host directory.
    """
    comment( "Make clean ...." )
    runCmd("cd ../lib/ ; make clean")

def cpMakefile ():
    """ copy dmakefile to database folder """
    if os.path.exists ( "database/Makefile" ):
        return
    cmd = "cp dmakefile database/Makefile"
    o = subprocess.getoutput ( cmd )

def cleanDatabase(dirname : str, verbose : bool ):
    """
    Clean up the database, e.g. remove orig and validation folders
    """
    fullpath = f"{dirname}/smodels-database"
    comment( f"Now cleaning up database in {fullpath}" )

    walker = os.walk( fullpath )
    for record in walker:
        File=record[0]
        # comment( "Now in %s: %s" %(File, record[1] ) )
        removals = [ "orig", ".git", "validation", "README.rst", "__pycache__", "moreValidation" ]
        rmFiles = [ "run_convert.sh", "checkFastlimValidation.py",  \
                    "checkFastlimValidation.ipynb", "convert.py","convertCMS.py", "sms.root", "exclusion_lines.json", "general.comment", "README", "convert.pyc", "unused_files.txt", "convertOld.py", "plotRatios.py", "plotRatios.sh", "ratios.txt" ]
        globs = glob.glob ( f"{File}/*log" )
        globs += glob.glob ( f"{File}/__pycache__" )
        globs += glob.glob ( f"{File}/*.py" )
        globs += glob.glob ( f"{File}/*.sh" )
        globs += glob.glob ( f"{File}/*.png" )
        globs += glob.glob ( f"{File}/*.rst" )
        globs += glob.glob ( f"{File}/*.pyc" )
        globs += glob.glob ( f"{File}/old*" )
        for g in globs:
            if not os.path.exists ( g ):
                continue
            if not "convert.py" in g and not "databaseParticles.py" in g:
                if os.path.isdir ( g ):
                    shutil.rmtree ( g )
                else:
                    os.unlink ( g )
        for r in removals:
            if r in File:
                cmd = f"rm -rf {File}"
                runCmd( cmd, prtMsg = False )
        for rf in rmFiles:
            fullpath = os.path.join( File, rf )
            if os.path.exists( fullpath):
                os.unlink( fullpath )
        clearJsons ( File, verbose )

def moveFastlim ( filename , dirname ):
    """
    Split up between the official database and fastlim database
    """
    comment( "Now move all fastlim entries in the database." )
    cwd=os.getcwd()
    comment( f"cwd: {cwd}", urgency = "debug" )
    comment( f"debug dirname: {dirname}", urgency = "debug" )
    cmd = f"cd {dirname}/smodels-database/; {cwd}/resultsMover.py"
    runCmd( cmd )
    cmd = f"mv ./smodels-fastlim.tgz {cwd}/{filename}-fastlim-1.0.tgz"
    runCmd( cmd )

def clearTxtFiles(dirname):
    clearGlobalInfos( f"{dirname}/smodels-database/" )
    clearGlobalInfos( "./smodels-fastlim/" )

def removePickles ( dirname ):
    """ remove the god damn pickle files """
    globs = glob.glob ( f"{dirname}/*.pcl" )
    globs = glob.glob ( f"{dirname}/*.rst" )
    globs = glob.glob ( f"{dirname}/*.log" )
    globs += glob.glob ( f"{dirname}/.*.pcl" )
    globs += glob.glob ( f"{dirname}/__pycache__" )
    globs += glob.glob ( f"{dirname}/**/*.pcl", recursive=True )
    globs += glob.glob ( f"{dirname}/**/*.rst", recursive=True )
    globs += glob.glob ( f"{dirname}/**/*.log", recursive=True )
    globs += glob.glob ( f"{dirname}/**/__pycache__", recursive=True )
    globs += glob.glob ( f"{dirname}/**/.*.pcl", recursive=True )
    print ( f"found {len(globs)} pickle files. removing them." )
    for g in globs:
        os.unlink ( g )

def createTarball(filename,dirname):
    """
    Create the tarball of smodels + database
    """
    comment( f"Create tarball {filename}.tgz from {dirname}"  )
    cmd = f"cp -r {dirname} {dirname}.backup"
    subprocess.getoutput ( cmd )
    removePickles ( dirname )
    runCmd( f"tar czvf {filename}.tgz {dirname}" )

def createDBTarball(filename,dirname):
    """
    Create the tarball of the database alone
    """
    comment( f"Create tarball {filename}.tgz" )
    removePickles ( dirname )
    runCmd( f"cd {dirname}; tar czvf {filename}.tgz smodels-database" )

def rmExtraFiles(dirname):
    """
    Remove additional files.
    """
    comment( "Remove a few unneeded files" )
    extras = [ "inputFiles/slha/nobdecay.slha", "inputFiles/slha/broken.slha",
               "docs/documentation/smodels.log", "inputFiles/slha/complicated.slha" ]
    for i in extras:
        cmd = f"rm -rf {dirname}/{i}"
        runCmd( cmd )

def convertRecipes(dirname):
    """
    Compile recipes from .ipynb to .py and .html.
    """
    comment( "Converting the recipes" )
    cmd = f"cd {dirname}/docs/manual/source/recipes/; make convert remove_ipynb"
    runCmd(cmd)

def makeDocumentation(dirname):
    """
    create the documentation via sphinx """
    comment( "Creating the documentation" )
    cmd = f"cd {dirname}/docs/manual/; make clean html; rm -r make.bat Makefile source "
    runCmd(cmd)
    cmd = f"cd {dirname}/docs/documentation/; make clean html; rm -r make.bat  Makefile source update"
    runCmd(cmd)

def explode(filename):
    """
    Explode the tarball.
    """
    comment( "Explode the tarball ..." )
    cmd = f"tar xzvf {filename}"
    runCmd(cmd)

def make(dirname):
    """
    Execute 'make' in dirname/lib.
    """
    comment( "Now run make in dirname/lib ..." )
    cmd = f"cd {dirname}/lib; make"
    runCmd(cmd)

def runExample(dirname):
    """
    Execute Example.py.
    """
    comment( "Now run Example.py ..." )
    cmd = f"cd {dirname}/; ./Example.py 2>&1 | tee out.log" 
    runCmd(cmd)
    comment( "Now check diff" )
    cmd = f"diff -u default.log {dirname}/out.log"
    d = runCmd( cmd )
    if len( d ) > 4:
        comment( "Example test failed!!", "error" )
    else:
        comment( "Looking good." )


def test(filename,dirname):
    """
    Test the tarball, explode it, execute 'make', and 'runSModelS.py'.
    """
    comment( "--------------------------" )
    comment( "    Test the setup ...    " )
    comment( "--------------------------" )
    rmdir(dirname)
    explode(f"{filename.strip()}.tgz")
    make(dirname)
    runExample(dirname)

def testDocumentation(dirname):
    """ Test the documentation """
    comment( "Test the documentation" )
    cmd=f"ls {dirname}/docs/manual/build/html/index.html"
    runCmd(cmd)

def createDBRelease(output,tag,reuse):
    """
    Create a tarball for distribution.
    :param reuse: reuse checked out database
    """

    dirname = output
    if os.path.isdir(dirname) and not reuse:
        comment( f"Folder ``{output}'' already exists. Remove it (i.e. run with -c) before creating the tarball {output}.tgz, or reuse, i.e. run with -r" )
        return False

    isDummy()
    if not reuse:
        rmlog(dirname) ## first remove the log file
        comment( f"Creating tarball for database distribution, version v{tag}" )
        rmdir(dirname)
        mkdir(dirname) ## .. then create the temp dir
        cpMakefile() ## copy Makefile if doesnt exist, for convenience only
        cloneDatabase(tag,dirname,dummyRun) ## git clone the database
    verbose = True
    cleanDatabase(dirname,verbose) ## clean up database, remove orig, validated
    clearTxtFiles(dirname) ## now clear up all txt files
    moveFastlim(output,dirname) ## split database into official and optional
    db = createDatabase ( dirname, reuse ) ## load the database
    removeNonValidated(db,dirname) ## remove all non-validated analyses
    moveNonAggregated(db,dirname) ## move all non-aggregated analyses to separate folder
    createDBTarball(output,dirname) ## here we go! create!
    isDummy()

def main():
    ap = argparse.ArgumentParser( description="makes a database tarball for public release" )
    ap.add_argument('-o', '--output', help='name of tarball filename [database]',
                    default="database" )
    ap.add_argument('-c', '--clear', help='remove output from previous run',
                    action="store_true" )
    ap.add_argument('-r', '--reuse', help='reuse already checked out database',
                    action="store_true" )
    f = open ( "../version", "rt" )
    ver = f.read().strip()
    f.close()
    ap.add_argument('-t', '--tag', help=f'database version [{ver}]', default=ver )
    ap.add_argument('-P', '--smodelsPath', help='path to the SModelS folder [None]',
                    default='../../smodels')

    args = ap.parse_args()
    if args.clear:
        cmd = "rm -rf database smodels-nonaggregated/ smodels-fastlim/"
        o = subprocess.getoutput ( cmd )
        print ( f"[createTarballs] {cmd}: {o}" )
    sys.path.insert(0,os.path.abspath(args.smodelsPath))
    createDBRelease( args.output, args.tag, args.reuse )

if __name__ == "__main__":
    main()

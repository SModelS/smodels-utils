#!/usr/bin/env python3

"""
.. module:: createTarballs
   :synopsis: Script that is meant to create the distribution tarballs

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys, subprocess, os, time, argparse, glob, shutil, colorama
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

def clone( dirname : str ):
    """
    Git clone smodels itself into dirname, then remove .git, .gitignore,
    distribution, and test.
    """
    comment( "Git-cloning smodels into %s(this might take a while)" % dirname )
    cmd = f"git clone --depth 1 -b {version} https://github.com/SModelS/smodels.git {dirname}"
#     cmd = "git clone git@smodels.hephy.at:smodels %s" %(dirname)
    if dummyRun:
        cmd = "cp -a ../../smodels-v%s/* %s" %( version, dirname )
    runCmd( cmd )
    for i in os.listdir( dirname ):
        if i in [".git", ".gitignore", "distribution", "test" ] or i.endswith ( ".pcl" ):
            runCmd( "rm -rf %s/%s" %(dirname,i) )

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
                cmd = "rm -rf %s" % File
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
    cmd = "cd %s/smodels-database/; %s/moveFastlimResults.py" % \
         ( dirname, cwd )
    runCmd( cmd )
    cmd = "mv ./smodels-fastlim.tgz %s/%s-fastlim-1.0.tgz" % \
         (cwd, filename)
    runCmd( cmd )

def clearTxtFiles(dirname):
    clearGlobalInfos( "%s/smodels-database/" % dirname )
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
    comment( "Create tarball %s.tgz from %s" % ( filename, dirname ) )
    cmd = f"cp -r {dirname} {dirname}.backup"
    subprocess.getoutput ( cmd )
    removePickles ( dirname )
    runCmd("tar czvf %s.tgz %s" %(filename, dirname))

def createDBTarball(filename,dirname):
    """
    Create the tarball of the database alone
    """
    comment( "Create tarball %s.tgz" %filename )
    removePickles ( dirname )
    runCmd("cd %s; tar czvf %s.tgz smodels-database" %(dirname, filename ))

def rmExtraFiles(dirname):
    """
    Remove additional files.
    """
    comment( "Remove a few unneeded files" )
    extras = [ "inputFiles/slha/nobdecay.slha", "inputFiles/slha/broken.slha",
               "docs/documentation/smodels.log", "inputFiles/slha/complicated.slha" ]
    for i in extras:
        cmd = "rm -rf %s/%s" %( dirname, i )
        runCmd( cmd )

def convertRecipes(dirname):
    """
    Compile recipes from .ipynb to .py and .html.
    """
    comment( "Converting the recipes" )
    cmd = "cd %s/docs/manual/source/recipes/; make convert remove_ipynb" % dirname
    runCmd(cmd)

def makeDocumentation(dirname):
    """
    create the documentation via sphinx """
    comment( "Creating the documentation" )
    cmd = "cd %s/docs/manual/; make clean html; rm -r make.bat Makefile source " % dirname
    runCmd(cmd)
    cmd = "cd %s/docs/documentation/; make clean html; rm -r make.bat  Makefile source update" % dirname
    runCmd(cmd)

def explode(filename):
    """
    Explode the tarball.
    """
    comment( "Explode the tarball ..." )
    cmd = "tar xzvf %s" %filename
    runCmd(cmd)

def make(dirname):
    """
    Execute 'make' in dirname/lib.
    """
    comment( "Now run make in dirname/lib ..." )
    cmd = "cd %s/lib; make" % dirname
    runCmd(cmd)

def runExample(dirname):
    """
    Execute Example.py.
    """
    comment( "Now run Example.py ..." )
    cmd = "cd %s/; ./Example.py 2>&1 | tee out.log" % dirname
    runCmd(cmd)
    comment( "Now check diff" )
    cmd = "diff -u default.log %s/out.log" % dirname
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
    explode(filename.strip()+'.tgz')
    make(dirname)
    runExample(dirname)

def testDocumentation(dirname):
    """ Test the documentation """
    comment( "Test the documentation" )
    cmd="ls %s/docs/manual/build/html/index.html" % dirname
    runCmd(cmd)

def createDBRelease(output,tag,reuse):
    """
    Create a tarball for distribution.
    :param reuse: reuse checked out database
    """

    dirname = output
    if os.path.isdir(dirname) and not reuse:
        comment("Folder ``%s'' already exists. Remove it (i.e. run with -c) before creating the tarball %s.tgz, or reuse, i.e. run with -r" %(output,output))
        return False

    isDummy()
    if not reuse:
        rmlog(dirname) ## first remove the log file
        comment( "Creating tarball for database distribution, version v%s" %tag )
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
        print ( "[createTarballs] %s: %s" % ( cmd, o ) )
    sys.path.insert(0,os.path.abspath(args.smodelsPath))
    createDBRelease( args.output, args.tag, args.reuse )

if __name__ == "__main__":
    main()

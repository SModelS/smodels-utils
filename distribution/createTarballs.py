#!/usr/bin/env python3

"""
.. module:: createTarballs
   :synopsis: Script that is meant to create the distribution tarballs

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys, subprocess, os, time, argparse, glob, shutil, colorama
from pathlib import Path
from distributionHelpers import clearGlobalInfo, runCmd, RED, GREEN, YELLOW, RESET
from smodels.experiment.databaseObj import Database
from typing import Union
sys.path.insert(0,"../")

dummyRun=False ## True

def comment( text, urgency="info" ):
    col=YELLOW
    pre=""
    if "err" in urgency.lower():
        pre="ERROR: "
        col=RED
    print("%s[%s] %s%s %s" %( col, time.asctime(), pre, text, RESET ))
    f=open("/tmp/create.log","a")
    f.write(  "[%s] %s\n" %( time.asctime(),text ) )
    f.close()
    if col == RED:
        sys.exit(-1)

def isDummy( ):
    if dummyRun:
        comment( "DUMMY RUN!!!!" )
    return dummyRun

def removeNonAggregated( db : Database, dirname : str, reuse : bool ):
    """ remove all non-aggregated analyses from
        database, and into smodels-nonaggregated """
    comment( f"starting removeNonAggregated" )
    if not os.path.exists ( "smodels-nonaggregated" ):
        os.mkdir ( "smodels-nonaggregated" )
    from smodels_utils.helper.databaseManipulations import filterNonAggregatedFromList
    # print ( f"now i need to remove all non-aggregated from {str(db)} dirname is {dirname} reuse is {reuse}" )
    ers = db.expResultList
    print ( f"@@@ now filtering non aggregated! {len(ers)}" )
    nonaggregated = filterNonAggregatedFromList ( ers, invert=True )
    print ( f"@@@ now filtering non aggregated! filtered: {len(nonaggregated)}" )
    for na in nonaggregated:
        path = na.globalInfo.path
        sqrts = float ( na.globalInfo.sqrts.asNumber() )
        if sqrts < 13.1:
            sqrts = int ( sqrts )
        from smodels_utils.helper.various import findCollaboration
        collaboration = findCollaboration ( na.globalInfo.id )
        path = path.replace ( "/globalInfo.txt", "" )
        newpath = f"smodels-nonaggregated/{sqrts}TeV/{collaboration}/"
        pathmaker = Path ( newpath )
        pathmaker.mkdir ( parents=True, exist_ok=True )
        cmd = f"mv {path} {newpath}"
        o = subprocess.getoutput ( cmd )
        print ( f"(re)moving {cmd}: {o}" )
        if os.path.exists ( path ):
            # if we couldnt move, we delete
            cmd = f"rm -r {path}"
    tarmaker = "tar czvf smodels-nonaggregated.tar.gz smodels-nonaggregated/*"
    o = subprocess.getoutput ( tarmaker )
    return db

def removeNonValidated( dirname : str, reuse : bool ):
    """ remove all non-validated analyses from
        database """
    comment( f"starting removeNonValidated" )
    load = "txt"
    if reuse:
        load = None
    comment( f"Now build the database pickle file: {load}" )
    d = Database( f"{dirname}/smodels-database", force_load = load,
                  progressbar=True )
    comment( "Now remove non-validated results." )
    ers = d.expResultList
    comment( "Loaded the database with %d results." %( len(ers) ) )
    for er in ers:
        if hasattr( er.globalInfo, "private" ) and er.globalInfo.private:
            comment( "%s is private. delete!" %( er.globalInfo.id ) )
            cmd = "rm -r %s" %( er.path )
            runCmd( cmd )
        else:
            hasDataSets=False
            for dataset in er.datasets:
                hasTxNames=False
                for txn in dataset.txnameList:
#                    if txn.validated in [ None, False ]:
                    if txn.validated in [ False ]:
                        #comment( "%s/%s/%s is not validated. Delete it." % \
                        #         ( er, dataset, txn ) )
                        cmd="rm '%s'" % txn.path
                        runCmd( cmd )
                    else:
                        hasTxNames=True
                if not hasTxNames:
                        comment( "%s/%s has no validated txnames. remove folder." %\
                                 (er, dataset ) )
                        cmd = "rm -r '%s'" % dataset.path
                        runCmd( cmd )
                if hasTxNames:
                    hasDataSets=True
            if not hasDataSets:
                comment( "%s has no validated datasets. remove folder." % \
                         (er) )
                cmd = "rm -rf %s" % er.path
                runCmd( cmd )
    base = d.subs[0].url
    # comment( "base=%s" % base )
    for tev in os.listdir( base ):
        fullpath = os.path.join( base, tev )
        if not os.path.isdir( fullpath ):
            continue
        tevHasResults=False
        for experiment in os.listdir( fullpath ):
            exppath = os.path.join( fullpath, experiment )
            if not os.path.isdir( exppath ):
                continue
            if os.listdir( exppath ) == []:
                comment( "%s/%s is empty. Delete it!" %( tev, experiment ) )
                cmd = "rm -rf %s" % exppath
                runCmd( cmd )
            else:
                tevHasResults=True
        if not tevHasResults:
            comment( "%s is empty. Delete it!" %( tev ) )
            cmd = "rm -rf %s" % fullpath
            runCmd( cmd )
    return d

def rmlog(dirname):
    """ clear the log file """
    cmd="rm -f /tmp/create.log"
    if os.path.isfile('create.log'):
        os.remove('create.log')
    if os.path.isfile('%s/smodels-database/create.log' %dirname):
        os.remove('%s/smodels-database/create.log' %dirname)

def mkdir(dirname):
    """
    Create a temporary directory for creating the tarball.
    """
    ## for i in( dirname, fastlimdir ):
    for i in( [ dirname ] ): ## , fastlimdir ):
        comment("Creating temporary directory %s" % i )
        runCmd( "mkdir -p %s" % i )

def rmdir(dirname):
    """
    Remove the temporary directories
    """
    for i in( dirname, ): ## fastlimdir ):
        if os.path.exists(i):
            comment( "Removing temporary directory %s" % i )
            runCmd("rm -rf %s" % i )

def clone(dirname):
    """
    Git clone smodels itself into dirname, then remove .git, .gitignore,
    distribution, and test.
    """
    comment( "Git-cloning smodels into %s(this might take a while)" % dirname )
    cmd = "git clone --depth 1 -b %s https://github.com/SModelS/smodels.git %s" %(version, dirname)
#     cmd = "git clone git@smodels.hephy.at:smodels %s" %(dirname)
    if dummyRun:
        cmd = "cp -a ../../smodels-v%s/* %s" %( version, dirname )
    runCmd( cmd )
    for i in os.listdir( dirname ):
        if i in [".git", ".gitignore", "distribution", "test" ] or i.endswith ( ".pcl" ):
            runCmd( "rm -rf %s/%s" %(dirname,i) )

def rmpyc(dirname):
    """
    Remove .pyc files.
    """
    comment( "Removing all pyc files ... " )
    runCmd("cd %s; rm -f *.pyc */*.pyc */*/*.pyc" % dirname )

def makeClean(dirname):
    """
    Execute 'make clean' in host directory.
    """
    comment( "Make clean ...." )
    runCmd("cd ../lib/ ; make clean")

def fetchDatabase(tag,dirname):
    """
    Execute 'git clone' to retrieve the database.
    """
    dbversion = tag
    comment( "git clone the database(this might take a while)" )
    ## "v" is not part of semver
    #cmd = "cd %s; git clone -b v%s git+ssh://git@github.com/SModelS/smodels-database.git"  % \
    if False:
        dbversion = "develop"
    cmd = "cd %s; git clone --depth 1 -b %s git+ssh://git@github.com/SModelS/smodels-database.git"  % \
           (dirname, dbversion)

    if dummyRun:
        cmd = "cd %s; cp -a ../../../smodels-database-v%s smodels-database" % \
             ( dirname, dbversion )
    runCmd( cmd )
    ## remove cruft
    rmcmd = "cd %s/smodels-database; " \
            "rm -rf .git .gitignore *.sh *.tar *.pyc; find *.py ! -name 'databaseParticles.py' -type f -exec rm -f {} +" % \
            ( dirname )
    runCmd( rmcmd )

def cpMakefile ():
    """ copy dmakefile to database folder """
    if os.path.exists ( "database/Makefile" ):
        return
    cmd = "cp dmakefile database/Makefile"
    o = subprocess.getoutput ( cmd )

def cleanDatabase(dirname : str ):
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
        clearJsons ( File )

def clearGlobalInfos(path):
    walker = os.walk(path)
    for record in walker:
        File=record[0]
        # print( "record=",record )
        for i in record[2]:
            if i[0]=="T" and i[-4:]==".txt":
                fullpath = os.path.join( File, i )
                clearGlobalInfo( fullpath )
        gIpath = os.path.join( File, "globalInfo.txt" )
        if os.path.exists( gIpath ):
            clearGlobalInfo( gIpath )

def splitDatabase(filename,dirname):
    """
    Split up between the official database and the optional database
    """
    comment( "Now move all the non-official entries in the database." )
    cwd=os.getcwd()
    comment( "debug cwd: %s" % cwd )
    comment( "debug dirname: %s" % dirname )
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
        fetchDatabase(tag,dirname) ## git clone the database
    cleanDatabase(dirname) ## clean up database, remove orig, validated
    clearTxtFiles(dirname) ## now clear up all txt files
    splitDatabase(output,dirname) ## split database into official and optional
    db=removeNonValidated(dirname,reuse) ## remove all non-validated analyses
    removeNonAggregated(db,dirname,reuse) ## remove all non-validated analyses
    createDBTarball(output,dirname) ## here we go! create!
    isDummy()

def create(output,tag):
    """
    Create a tarball for distribution.
    """

    dirname = output
    if os.path.isdir(dirname):
        comment('Folder %s already exists. Remove it before creating the tarball %s.tgz' %(output,output))
        return False
    isDummy()
    rmlog() ## first remove the log file
    comment( "Creating tarball for distribution, version %s" % version )
    makeClean(dirname)
    rmdir(dirname)
    mkdir(dirname) ## .. then create the temp dir
    clone(dirname) ## ... clone smodels into it ...
    fetchDatabase(tag,dirname) ## git clone the database
    cleanDatabase(dirname) ## clean up database, remove orig, validated
    # sys.exit()
    splitDatabase(otuput,dirname) ## split database into official and optional
    removeNonValidated(dirname) ## remove all non-validated analyses
    clearTxtFiles(dirname) ## now clear up all txt files
    convertRecipes(dirname)
    makeDocumentation(dirname)
    rmExtraFiles(dirname) ## ... remove unneeded files ...
    rmpyc(dirname) ## ...  remove the pyc files created by makeDocumentation ...
    rmlog(dirname)  ##Make sure to remove log files
    createTarball(output,dirname) ## here we go! create!
    test(output,dirname)
    # rmdir(dirname)
    testDocumentation(dirname)
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
        cmd = "rm -rf database"
        o = subprocess.getoutput ( cmd )
        print ( "[createTarballs] %s: %s" % ( cmd, o ) )
    sys.path.insert(0,os.path.abspath(args.smodelsPath))
    createDBRelease( args.output, args.tag, args.reuse )

if __name__ == "__main__":
    main()

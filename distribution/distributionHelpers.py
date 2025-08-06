#!/usr/bin/env python3

"""
.. module:: distributionHelpers
   :synopsis: functions that help with tarball creation

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import subprocess, os, glob, time
from smodels.experiment.databaseObj import Database
from pathlib import Path
from typing import Union
from smodels_utils.helper.terminalcolors import *

def comment( text : str, urgency : str = "info" ):
    """ comment on what you are doing """
    urgency = urgency.lower()
    col=YELLOW
    pre=""
    if "err" in urgency:
        pre="ERROR: "
        col=RED
    if not "deb" in urgency:
        print( f"{col}[{time.asctime()}] {pre}{text} {RESET}" )
    f=open("./create.log","at")
    f.write( f"[{time.asctime()}] {text}\n" )
    f.close()
    if col == RED:
        sys.exit(-1)

def runCmd ( cmd : str, prtMsg : bool = True ):
    """ run a certain command """
    cmd=cmd.strip()
    if prtMsg:
        print( f"{GREEN}[cmd] {cmd}{RESET}" )
    f=open("/tmp/create.log","a")
    f.write( f"cmd: {cmd}\n" )
    # print('CMD=',cmd)
    o=(subprocess.check_output( cmd, shell=True )).decode("utf-8")
    if len(o)>0:
        print(f"[distribution] {o:>.80}" )
        f.write( f"{o!s}\n" )
    f.close()
    return str(o)


def clearGlobalInfo( filename : str ):
    """ tidy up a given global info file """
    # print ( "[createTarballs] checking", filename )
    f=open(filename)
    lines=f.readlines()
    f.close()
    # fname = "/tmp/tmp.txt"
    fname = "/dev/shm/tmp.txt"
    g=open( fname,"wt")
    skip = [ "publishedData", "comment", "private", "checked", "xrange", \
             "prettyName", "susyProcess", "dataUrl", "validationTarball", "yrange",
             "bsmProcess", "resultType" ]
    #skip.append( "validated" )
    # skip.append( "axes" )
    # skip.append( "figureUrl" )
    for line in lines:
        to_skip = False
        p1 = line.find("#")
        if p1 == 0:
            to_skip = True
        for s in skip:
            if line.find(s)==0:
                to_skip = True
        if not to_skip:
            g.write( line )
    g.close()
    cmd = f"cp {fname} {filename}"
    runCmd( cmd, prtMsg=False )

def clearJsons ( path : str, verbose : bool ):
    """ clear the jsons in the given path. look at globalInfo.txt
        which jsons get used. ditch the rest. """
    gI = f"{path}/globalInfo.txt"
    rpath = path[path.rfind("/")+1:]
    if not os.path.exists ( gI ):
        return
    usedJsons = set()
    f = open ( gI, "rt" )
    lines = f.readlines()
    f.close()
    from smodels.experiment.expAuxiliaryFuncs import concatenateLines
    lines = concatenateLines ( lines )
    from icecream import ic
    for i,line in enumerate(lines):
        p1 = line.find("#")
        if p1 >= 0:
            line = line[:p1]
        line = line.strip()
        if line == "":
            continue
        if not "jsonFiles:" in line and not "jsonFiles_FullLikelihood:" in line:
            continue
        txt = line.replace("jsonFiles:","")
        txt = txt.replace("jsonFiles_FullLikelihood:","")
        try:
            D = eval(txt)
        except Exception as e:
            D = {}
        for k in D.keys():
            usedJsons.add ( k )
    jsons = glob.glob ( f"{path}/*.json" )
    ctRemoved = 0
    for js in jsons:
        fname = os.path.basename ( js )
        remove = fname not in usedJsons
        if remove:
            if verbose:
                ko = f"keeping only {','.join(usedJsons)}"
                if len(usedJsons)==0:
                    ko = "no pyhf models used"
                comment ( f"removing {fname} in {rpath}: {ko}" )
            ctRemoved += 1
            os.unlink ( js )
    if ctRemoved>0:
        comment ( f"removed {ctRemoved} json files in {rpath}" )

def hasNonValidated ( ers ):
    """ FIXME remove when not anymore used! """
    hasNonValidated = False
    for er in ers:
        dss = er.datasets
        for ds in dss:
            for txn in ds.txnameList:
                if txn.validated == False:
                    hasNonValidated = True
    return hasNonValidated

def removeNonValidated( db : Database, dirname : str = "database/" ):
    """ remove all non-validated analyses from text database """
    comment( f"starting removeNonValidated" )
    comment( "Now remove non-validated results." )
    ers = db.getExpResults ( useNonValidated = True )
    comment( f"Loaded the database with {len(ers)} results." )
    for er in ers:
        if hasattr( er.globalInfo, "private" ) and er.globalInfo.private:
            comment( f"{er.globalInfo.id} is private. delete!" )
            cmd = f"rm -r {er.path}"
            runCmd( cmd )
        else:
            hasDataSets=False
            for dataset in er.datasets:
                hasTxNames=False
                for txn in dataset.txnameList:
#                    if txn.validated in [ None, False ]:
                    if txn.validated in [ False ]:
                        comment( f"{er}/{dataset}/{txn} is not validated. Delete it." )
                        cmd=f"rm '{txn.path}'"
                        runCmd( cmd )
                    else:
                        hasTxNames=True
                if not hasTxNames:
                        comment( "%s/%s has no validated txnames. remove folder." %\
                                 (er, dataset ) )
                        cmd = f"rm -r '{dataset.path}'"
                        runCmd( cmd )
                if hasTxNames:
                    hasDataSets=True
            if not hasDataSets:
                comment( f"{er} has no validated datasets. remove folder." )
                cmd = f"rm -rf {er.path}"
                runCmd( cmd )
    base = db.subs[0].url
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
                comment( f"{tev}/{experiment} is empty. Delete it!" )
                cmd = f"rm -rf {exppath}"
                runCmd( cmd )
            else:
                tevHasResults=True
        if not tevHasResults:
            comment( f"{tev} is empty. Delete it!" )
            cmd = f"rm -rf {fullpath}"
            runCmd( cmd )
    return db

def createDatabase ( dirname : str = "database/", reuse : bool = True ):
    """ very simple convenience function to centrally load database """
    load = "txt"
    if reuse:
        load = None
    comment( f"Now build the database pickle file: {dirname}" )
    db = Database( f"{dirname}/smodels-database", force_load = load,
                  progressbar=True )
    return db

def moveNonAggregated( db : Database, dirname : str = "database/", 
                       destination : str = "smodels-nonaggregated/" ):
    """ move all non-aggregated analyses from
        database, and into smodels-nonaggregated """
    comment( f"starting moveNonAggregated" )
    if not os.path.exists ( destination ):
        os.mkdir ( destination )
    from smodels_utils.helper.databaseManipulations import filterNonAggregatedFromList
    # print ( f"now i need to remove all non-aggregated from {str(db)} dirname is {dirname} reuse is {reuse}" )
    ers = db.getExpResults ( useNonValidated = True )
    nonaggregated = filterNonAggregatedFromList ( ers, invert=True )
    comment( f"now filtering non aggregated: {len(nonaggregated)}/{len(ers)}" )
    for na in nonaggregated:
        path = na.globalInfo.path
        sqrts = float ( na.globalInfo.sqrts.asNumber() )
        if sqrts < 13.1:
            sqrts = int ( sqrts )
        from smodels_utils.helper.various import getCollaboration
        collaboration = getCollaboration ( na.globalInfo.id )
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
    tarball = "../smodels-nonaggregated.tar.gz"
    tarmaker = f"cd smodels-nonaggregated; tar czvf {tarball} ./"
    o = subprocess.getoutput ( tarmaker )
    comment ( f"created {tarball}" )
    return db

def cloneDatabase( tag : str = "3.1.0", dirname : os.PathLike = "database/",
       pretend : bool = False ):
    """
    Execute 'git clone' to retrieve the database.
    """
    dbversion = tag
    comment( "git clone the database(this might take a while)" )
    pathmaker = Path ( dirname )
    pathmaker.mkdir ( parents=True, exist_ok=True )
    ## "v" is not part of semver
    #cmd = "cd %s; git clone -b v%s git+ssh://git@github.com/SModelS/smodels-database.git"  % \
    if False:
        dbversion = "develop"
    cmd = f"cd {dirname}; git clone --depth 1 -b {dbversion} git+ssh://git@github.com/SModelS/smodels-database.git"

    if pretend:
        cmd = f"cd {dirname}; cp -a ../../../smodels-database-v{dbversion} smodels-database"
    runCmd( cmd )

    comment( "create hep json file" )
    import createHepJson
    # createHepJson.create ( f"{dirname}/smodels-database", f"{dirname}/smodels-database/smodels-analyses.json" )

    comment( "remove cruft" )
    ## remove cruft
    rmcmd = f"cd %s/smodels-database; " \
            "rm -rf .git .gitignore *.sh *.tar *.pyc; find *.py ! -name 'databaseParticles.py' -type f -exec rm -f {} +" % \
            ( dirname )
    runCmd( rmcmd )

def clearGlobalInfos( path : str ):
    """ clear all globalInfos.txt files under path """
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

if __name__ == "__main__":
    # intended to be whatever it is you need right now
    cloneDatabase ( )
    db = createDatabase ( )
    removeNonValidated ( db )
    moveNonAggregated ( db )

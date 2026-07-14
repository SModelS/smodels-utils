#!/usr/bin/env python3

"""
.. module:: publishDatabasePickle
   :synposis: makes database pickle files publically available. FIXME this
   script should be split in two: one script that prepares all pickles
   (official, fastlim, nonaggregated, superseded, full_llhds),
   another script that uploads them and writes the jsons

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

from __future__ import print_function
import pickle, os, sys, argparse, time, copy, glob
import hashlib
import pathlib
import gzip, shutil
from smodels_utils.helper.terminalcolors import *
from smodels.base.runtime import checkForIncompatibleModuleVersions

from typing import Union, Set, Tuple

# everything should be numpy>=2.x by now
# from smodels_utils.helper.various import checkNumpyVersion
# checkNumpyVersion()
smodels_check = checkForIncompatibleModuleVersions()
if not smodels_check:
    sys.exit()

if sys.version[0]=="2":
    import commands as CMD
else:
    import subprocess as CMD

def pprint ( *args ):
    print ( f"[publishDatabasePickle] {CYAN}", *args, RESET )

def sizeof_fmt(num, suffix='B'):
    for unit in [ '','K','M','G','T','P' ]:
        if abs(num) < 1024.:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def prepareCommandsFile ( ) :
    """ prepare the commands.sh file """
    f=open( "commands.sh", "wt" )
    f.write ( "#!/bin/sh\n" )
    f.write ( f"# created {time.asctime()}\n\n" )
    f.close( )
    os.chmod ( "commands.sh", 0o755 )

def addToCommandsFile ( cmd ):
    f=open( "commands.sh", "at" )
    f.write ( f"{cmd}\n" )
    f.close()

def _getSHA1 ( filename : os.PathLike ) -> str:
    return hashlib.sha1( pathlib.Path(filename).read_bytes() ).hexdigest()

eosdir = "/eos/project/s/smodels/www/database/"

def createInfoFile ( infofile : str, pclfilename : str ):
    """ create the file with the python dictionary that contains all
    meta info about the pickle file, e.g.:
    {
        "lastchanged": 1746624990.8478498,
        "mtime": "Wed May  7 15:36:30 2025",
        "size": 90289590,
        "url": "https://smodels.web.cern.ch/smodels/database/unittest310.pcl",
        "sha1": "5b7d238b401aab442e7944c6afdbb31e9b4c444c"
    }
    :param infofile: path to info file containing above python dictionary
    :param pclfilename: path to pickle file
	  """
    f=open ( infofile, "w" )
    ## for the time stamp we had modification time of pickle file
    ## lets try last modification time of info file instead, might be
    ## more conservative (i.e. triggers downloads faster)
    sha = _getSHA1 ( pclfilename )
    lastchanged = time.time()
    mtime = time.asctime(time.localtime(lastchanged))
    baseurl = "https://smodels.web.cern.ch/smodels/database"
    Dict = { "lastchanged": lastchanged, "mtime": mtime,
             "size": os.stat(pclfilename).st_size,
             "url": f"{baseurl}/{pclfilename}", "sha1": sha }
    from ptools.helpers import py_dumps
    ds = py_dumps ( Dict, double_quotes = True )
    f.write ( ds+ "\n" )
    # f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()

def checkNonValidated( database ) -> Tuple[bool,Set]:
    """ check if there are results with e.g. "tbd" as their validated field.
    """
    has_nonValidated = False
    expResults = database.getExpResults( useNonValidated=True )
    has_nonValidated = False
    nonValidateds = set()
    for e in expResults:
        for ds in e.datasets:
            for tx in ds.txnameList:
                if tx.validated in [ False, True, "N/A", "n/a" ]:
                    continue
                sds = str(ds).replace("Dataset ","")
                pprint ( f"{RED}Non-validated result: {e.globalInfo.id}{RESET}:{sds}, {tx}: {tx.validated} " )
                has_nonValidated = True
                nonValidateds.add ( e.globalInfo.id )
    return has_nonValidated, nonValidateds

def main():
    descr="makes a database pickle file publically available (creating via SModelS)"
    ap = argparse.ArgumentParser( description=descr )
    ap.add_argument( '-f', '--filename',
        help='name of pickle file [database.pcl]',
        default="database.pcl" )
    ap.add_argument( '--db_name',
        help='give an explicit name for this database [auto]', default=None )
    ap.add_argument('-d', '--dry_run',
        help='dont copy to final destination',
        action="store_true" )
    ap.add_argument('-l', '--latest',
        help='define as latest database',
        action="store_true" )
    ap.add_argument('-b', '--build',
        help='build pickle file, assume filename is directory name',
        action="store_true" )
    ap.add_argument('-t', '--txnamevalues',
        help='when building, add txname values',
        action="store_true" )
    ap.add_argument('-r', '--remove_fastlim',
        help='build pickle file, remove fastlim results',
        action="store_true" )
    ap.add_argument('-y', '--remove_yields_only',
        help='build pickle file, remove yields only results',
        action="store_true" )
    ap.add_argument('-s', '--remove_superseded',
        help='build pickle file, remove superseded results',
        action="store_true" )
    ap.add_argument('-a', '--remove_nonaggregated',
        help='build pickle file, remove nonaggregated results',
        action="store_true" )
    ap.add_argument( '--full_llhds',
        help='create also full llhds pickle file',
        action="store_true" )
    ap.add_argument('-P', '--smodelsPath',
        help='path to the SModelS folder [None]',
        default=None )
    ap.add_argument('-V', '--skipValidation',
        help='if set will skip the check of validation flags [False]',
        default=False, action="store_true" )
    ap.add_argument ( '-i', '--ignore',
        help='ignore the validation flags of analysis (i.e. also add non-validated results)',
        action='store_true' )
    ap.add_argument ( '-p', '--prepare_commands',
        help='prepare the commands file', action='store_true' )
    ap.add_argument ( '-F', '--finalize_commands',
        help='finalize the commands file', action='store_true' )
    args = ap.parse_args()
    if args.prepare_commands:
        prepareCommandsFile()
    dbname = args.filename
    if args.smodelsPath:
        sys.path.append(os.path.abspath(args.smodelsPath))

    from smodels_utils.helper.databaseManipulations import removeFastLimFromDB,\
        removeSupersededFromDB, removeNonAggregatedFromDB,\
        selectFullLikelihoodsFromDB, removeYieldsOnlyFromDB

    has_nonValidated = False
    nonValidated = []
    fastlim = True
    picklefile = dbname
    from smodels.experiment.databaseObj import Database
    if not args.build:
        d = Database ( dbname )
        dbver = d.databaseVersion
        picklefile = dbname
    else:
        if not os.path.isdir ( dbname ):
            print ( f"supplied --build option, but {dbname} is not a directory." )
            sys.exit()
        tarballs = glob.glob ( f"{dbname}/*.tar.gz" )
        tarballs += glob.glob ( f"{dbname}/*.tgz" )
        if len(tarballs)>0:
            t = [ x.replace(f"{dbname}/","").replace(dbname,"") for x in tarballs ]
            print ( f"there are tarballs [{','.join(t)}] in {dbname}. Will explode them." )
            for t in tarballs:
                shutil.unpack_archive( filename=t, extract_dir=dbname)
        force_load = None
        if args.txnamevalues:
            pprint ( "building with txname values!" )
            import smodels.experiment.txnameObj
            smodels.experiment.txnameObj.TxNameData._keep_values = True
            force_load = "txt"
        import smodels
        pprint ( f"building database ''{dbname}'' with ''{os.path.dirname ( smodels.__file__ )}''" )
        d = Database ( dbname, progressbar=True, force_load = force_load )
        ers = d.getExpResults()
        assert len(ers)>0, f"no experimental results in database?"
        er0 = d.getExpResults()[0]
        assert len(er0.datasets)>0, f"no datasets in {er0.globalInfo.id}?"
        ds0 = er0.datasets[0]
        if len(ds0.txnameList)>0:
            txn0 = ds0.txnameList[0]
            txnd = txn0.txnameData
            if args.txnamevalues:
                if not hasattr ( txnd, "origdata" ):
                    pprint ( "FATAL: why arent there origdata in tnamedata??" )
                    sys.exit()
            else:
                if hasattr ( txnd, "origdata" ):
                    pprint ( "we have orig data! lets repickle with force_load = txt" )
                    force_load = "txt"
                    d = Database ( dbname, progressbar=True, force_load = force_load )
                    ds0 = d.getExpResults()[0].datasets[0]
                    txn0 = ds0.txnameList[0]
                    txnd = txnd.txnameData
                    if hasattr ( txnd, "origdata" ):
                        pprint ( "FATAL: we still have orig data!" )
                        sys.exit()


        dbver = d.databaseVersion
        picklefile = os.path.join ( dbname, d.txt_meta.getPickleFileName() )

    if args.remove_superseded:
        # e = copy.deepcopy( d )
        e = Database ( picklefile, progressbar=True )
        e2 = removeSupersededFromDB ( e, invert=True, outfile="superseded.pcl" )
        pprint ( f"superseded database is called {e.databaseVersion}" )
        d = removeSupersededFromDB ( d )
    if args.remove_fastlim:
        # e = copy.deepcopy( d )
        e = Database ( picklefile, progressbar=True )
        ## create fastlim only
        e = removeFastLimFromDB ( e, invert = True, picklefile = "fastlim.pcl" )
        d = removeFastLimFromDB ( d, picklefile = "official.pcl" )
        d.pcl_meta.hasFastLim = False
        d.txt_meta.hasFastLim = False
        d.subs[0].databaseVersion = dbver # .replace("fastlim","official")
        e.subs[0].databaseVersion=f"fastlim{dbver}"
        del e
    if args.remove_nonaggregated:
        # e = copy.deepcopy( d )
        e = Database ( picklefile, progressbar=True )
        ## create fastlim only
        e = removeNonAggregatedFromDB ( e, invert = True,
                picklefile = "nonaggregated.pcl" )
        d = removeNonAggregatedFromDB ( d, picklefile = "official.pcl" )
        d.pcl_meta.hasFastLim = False
        d.txt_meta.hasFastLim = False
        d.subs[0].databaseVersion = dbver # .replace("fastlim","official")
        e.subs[0].databaseVersion=f"nonaggregated{dbver}"
        del e
    if args.remove_yields_only:
        # e = copy.deepcopy( d )
        e = Database ( picklefile, progressbar=True )
        ## create fastlim only
        e = removeYieldsOnlyFromDB ( e, invert = True,
                picklefile = "yields_only.pcl" )
        d = removeYieldsOnlyFromDB ( d, picklefile = "official.pcl" )
        # d.pcl_meta.hasFastLim = False
        # d.txt_meta.hasFastLim = False
        d.subs[0].databaseVersion = dbver # .replace("fastlim","official")
        e.subs[0].databaseVersion=f"yields_only{dbver}"
        del e
    if args.full_llhds:
        f = Database ( picklefile, progressbar=True )
        f = selectFullLikelihoodsFromDB ( f,
                picklefile = "full_llhds.pcl" )
        f.subs[0].databaseVersion=dbver
        pprint ( f"dbver {dbver} ver {f.databaseVersion}" )
        del f

    if not args.skipValidation:
        validated, which = checkNonValidated(d)
        has_nonValidated = validated
    else:
        has_nonValidated = False

    p=open(picklefile,"rb")
    meta=pickle.load(p)
    p.close()
    fastlim = meta.hasFastLim
    if args.remove_fastlim:
        fastlim = False
    pprint ( f"\n{meta}" )
    ver = meta.databaseVersion
    if type(ver) == str:
        ver = ver.replace(".","")
    else:
        ver = str(ver)
    sfastlim=""
    if fastlim:
        sfastlim="_fastlim"

    infofile = f"official{ver}{sfastlim}"
    pclfilename = f"official{ver}{sfastlim}.pcl"
    if args.db_name not in [ "auto", None ]:
        pclfilename = args.db_name + ".pcl"
        infofile = args.db_name
    if args.txnamevalues:
        d.subs[0].databaseVersion=f"debug{dbver}"
        infofile = f"debug{ver.replace('debug', '')}"
        pclfilename = f"debug{ver.replace('debug', '')}.pcl"
    if "nonaggregated" in ver:
        infofile = f"nonaggregated{ver.replace('nonaggregated', '')}"
        pclfilename = f"nonaggregated{ver.replace('nonaggregated', '')}.pcl"
    if "yieldsonly" in ver:
        infofile = f"yieldsonly{ver.replace('yieldsonly', '')}"
        pclfilename = f"yieldsonly{ver.replace('yieldsonly', '')}.pcl"
    if "full_llhds" in ver:
        infofile = f"full_llhds{ver.replace('full_llhds', '')}"
        pclfilename = f"full_llhds{ver.replace('full_llhds', '')}.pcl"
    if "superseded" in ver:
        infofile = f"superseded{ver.replace('superseded', '')}"
        pclfilename = f"superseded{ver.replace('superseded', '')}.pcl"
    if "fastlim" in ver:
        # infofile = "fastlim%s" % ( ver.replace("fastlim","") )
        #pclfilename = "fastlim%s.pcl" % ( ver.replace("fastlim","") )
        infofile = ver
        pclfilename = f"{ver}.pcl"

    if ver == "unittest":
        smodels_ver = ver # "300"
        infofile = f"unittest{smodels_ver}"
        pclfilename = f"{infofile}.pcl"
    else:
        if "unittest" in ver:
            smodels_ver = ver.replace("unittest","")
            infofile = f"unittest{smodels_ver}"
            pclfilename = f"{infofile}.pcl"

    #cmd = "cp %s ./%s" % ( picklefile, pclfilename )
    ssh = True
    if os.path.exists ( eosdir ): ## eos exists locally? copy!
        ssh = False
    pprint ( f"writing {pclfilename}" )
    d.createBinaryFile ( pclfilename )
    sze = sizeof_fmt ( os.stat(pclfilename).st_size )
    sha1sum = _getSHA1 ( pclfilename )
    pprint ( f"database size {sze} sha1sum {sha1sum}" )
    createInfoFile ( infofile, pclfilename ) # , meta.mtime )
    if has_nonValidated:
        nvlist = ",".join(which)
        if args.ignore:
            print ( f"has non-validated results ({nvlist}), but you requested to continue." )
        else:
            print ( f"has non-validated results ({nvlist}). Stopping the procedure." )
            sys.exit()
    del d
    sexec="executing:"
    if args.dry_run:
        sexec="suppressing execution of:"
    if not ssh:
        print ( "eos exists on this machine! copy file!" )
        cmd = f"cp {pclfilename} {eosdir}/"
        a=CMD.getoutput ( cmd )
        if len(a)>0:
            pprint ( f"{a}" )
    cmd = f"mv {infofile} ../../smodels.github.io/database/{infofile}"
    pprint ( f"{sexec} {cmd}" )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )

    if args.latest:
        latestfile = "latest"
        if not args.remove_fastlim:
            latestfile = "latest_fastlim"
        cmd = f"cp ../../smodels.github.io/database/{infofile} ../../smodels.github.io/database/{latestfile}"
        if not args.dry_run:
            a=CMD.getoutput ( cmd )
            pprint ( f"update latest: {cmd} {a}" )
    backupfile = None
    if args.db_name is None and not args.txnamevalues and not "superseded" in ver and not "full_llhds" in ver and not "nonaggregated" in ver and not "fastlim" in ver: # build the backup version
        backupfile = f"backup{ver}"
        #if not args.remove_fastlim:
        #    backupfile = "backup_fastlim"
        cmd = "cp ../../smodels.github.io/database/%s ../../smodels.github.io/database/%s" %\
               ( infofile, backupfile )
        if not args.dry_run:
            a=CMD.getoutput ( cmd )
            pprint ( f"update backup: {cmd} {a}" )
    cmd = f"cd ../../smodels.github.io/; git pull; git add database/{infofile}; "
    if backupfile != None:
        cmd += f"git add database/{backupfile}; "
    if args.latest:
        cmd += f"git add database/{latestfile}; "
    cmd += "git commit -m 'auto-commited by publishDatabasePickle.py'; git push"
    if args.dry_run:
        print ( f"suppressing execution of: {cmd}" )
    else:
        a=CMD.getoutput ( cmd )
        print ( a )

    home = os.environ["HOME"]
    if ssh and not args.dry_run:
        # 2FA, so just moved them into cernbox, we take it from there
        # cmd2 = f"scp {pclfilename} lxplus.cern.ch:{eosdir}{pclfilename}"
        cmd2 = f"mv {pclfilename} ~/cernbox/tmp_dbs/"
        # print ( f"{RED}[publishDatabasePickle] Now please execute manually (and I copied the command to your clipboard):{RESET}" )
        pprint ( f"running: {cmd2}" )
        reallyDo = not args.dry_run
        # reallyDo = False # doesnt work no more
        if reallyDo:
            o = CMD.getoutput ( cmd2 )
            pprint ( f"{cmd2}: {o}" )
        addToCommandsFile ( cmd2 )
        #o = CMD.getoutput ( f"echo '{cmd2}' | xsel -i" )
        if not reallyDo:
            pprint ( f"NOT done (because commands.sh): {cmd2}" )
        print ( )
        # pprint ( "(have to do this by hand, if no password-less ssh is configured)" )
        cmd = f"ssh lxplus.cern.ch smodels/www/database/create.py"
        pprint ( f"now do -- pasted to clipboard:\n{cmd}" )
        o = CMD.getoutput ( f"echo '{cmd}' | xsel -i" )
        #if reallyDo:
        #    o = CMD.getoutput ( cmd )
        #    pprint ( f"done: {cmd}: {o}" )
        if args.finalize_commands:
            addToCommandsFile ( cmd )
        print ( )
        print ( "now point your browser to: " )
        print ( "https://smodels.web.cern.ch/smodels/database/" )

main()

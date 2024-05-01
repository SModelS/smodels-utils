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
from colorama import Fore as ansi

if sys.version[0]=="2":
    import commands as CMD
else:
    import subprocess as CMD

def sizeof_fmt(num, suffix='B'):
    for unit in [ '','K','M','G','T','P' ]:
        if abs(num) < 1024.:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def prepareCommandsFile ( ) :
    """ prepare the commands.sh file """
    f=open( "commands.sh", "wt" )
    f.write ( "#!/bin/sh\n" )
    f.write ( f"# created {time.asctime()}\n\n" )
    f.close( )
    os.chmod ( "commands.sh", 0o755 )

def addToCommandsFile ( cmd ):
    f=open( "commands.sh", "at" )
    f.write ( cmd + "\n" )
    f.close()

def _getSHA1 ( filename ):                                                                         return hashlib.sha1( pathlib.Path(filename).read_bytes() ).hexdigest()

eosdir = "/eos/project/s/smodels/www/database/"

def createInfoFile ( infofile, pclfilename, lastchanged ):
    f=open ( infofile, "w" )
    mtime = time.asctime(time.localtime(lastchanged))
    sha = _getSHA1 ( pclfilename )
    Dict = { "lastchanged": lastchanged, "mtime": mtime, "size": os.stat(pclfilename).st_size,
             "url": "https://smodels.web.cern.ch/smodels/database/%s" % pclfilename,
             "sha1": sha }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()

def checkNonValidated( database ):
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
                print ( f"[publishDatabasePickle] {ansi.RED}Non-validated result: {e.globalInfo.id}{ansi.RESET}:{str(ds)}, {tx}: {tx.validated} " )
                has_nonValidated = True
                nonValidateds.add ( e.globalInfo.id )
    return has_nonValidated, nonValidateds

def main():
    ap = argparse.ArgumentParser( description="makes a database pickle file publically available (run it on the smodels)" )
    ap.add_argument('-f', '--filename', help='name of pickle file [database.pcl]', default="database.pcl" )
    ap.add_argument('-d', '--dry_run', help='dont copy to final destination', action="store_true" )
    ap.add_argument('-l', '--latest', help='define as latest database', action="store_true" )
    ap.add_argument('-b', '--build', help='build pickle file, assume filename is directory name', action="store_true" )
    ap.add_argument('-t', '--txnamevalues', help='when building, add txname values', action="store_true" )
    ap.add_argument('-r', '--remove_fastlim', help='build pickle file, remove fastlim results', action="store_true" )
    ap.add_argument('-s', '--remove_superseded', help='build pickle file, remove superseded results', action="store_true" )
    ap.add_argument('-a', '--remove_nonaggregated', help='build pickle file, remove nonaggregated results', action="store_true" )
    ap.add_argument( '--full_llhds', help='create also full llhds pickle file', action="store_true" )
    ap.add_argument('-P', '--smodelsPath', help='path to the SModelS folder [None]', default=None )
    ap.add_argument('-V', '--skipValidation', help='if set will skip the check of validation flags [False]', default=False, action="store_true" )
    ap.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
    ap.add_argument ( '-p', '--prepare_commands', help='prepare the commands file', action='store_true' )
    ap.add_argument ( '-F', '--finalize_commands', help='finalize the commands file', action='store_true' )
    args = ap.parse_args()
    if args.prepare_commands:
        prepareCommandsFile()
    dbname = args.filename
    if args.smodelsPath:
        sys.path.append(os.path.abspath(args.smodelsPath))

    from smodels.experiment.databaseObj import Database
    try:
        from smodels_utils.helper.databaseManipulations import removeFastLimFromDB, removeSupersededFromDB, removeNonAggregatedFromDB, selectFullLikelihoodsFromDB
    except ModuleNotFoundError:
        sys.path.append('../')
        from smodels_utils.helper.databaseManipulations import removeFastLimFromDB, removeSupersededFromDB, removeNonAggregatedFromDB


    has_nonValidated = False
    nonValidated = []
    fastlim = True
    picklefile = dbname
    if not args.build:
        d = Database ( dbname )
        dbver = d.databaseVersion
        picklefile = dbname
    else:
        if not os.path.isdir ( dbname ):
            print ( "supplied --build option, but %s is not a directory." % dbname )
            sys.exit()
        tarballs = glob.glob ( f"{dbname}/*.tar.gz" )
        tarballs += glob.glob ( f"{dbname}/*.tgz" )
        if len(tarballs)>0:
            t = [ x.replace(dbname+"/","").replace(dbname,"") for x in tarballs ]
            print ( f"there are tarballs [{','.join(t)}] in {dbname}. Will explode them." )
            for t in tarballs:
                shutil.unpack_archive( filename=t, extract_dir=dbname)
        force_load = None
        if args.txnamevalues:
            print ( "[publishDatabasePickle] building with txname values!" )
            import smodels.experiment.txnameObj
            smodels.experiment.txnameObj.TxNameData._keep_values = True
            force_load = "txt"
        import smodels
        print ( "[publishDatabasePickle] building database ''%s'' with ''%s''" % \
                (dbname, os.path.dirname ( smodels.__file__ ) ) )
        d = Database ( dbname, progressbar=True, force_load = force_load )
        if args.txnamevalues:
            txnd = d.getExpResults()[0].datasets[0].txnameList[0].txnameData
            if not hasattr ( txnd, "origdata" ):
                print ( "[publishDatabasePickle] FATAL: why arent there origdata in tnamedata??" )
                sys.exit()
        else:
            txnd = d.getExpResults()[0].datasets[0].txnameList[0].txnameData
            if hasattr ( txnd, "origdata" ):
                print ( "[publishDatabasePickle] we have orig data! lets repickle with force_load = txt" )
                force_load = "txt"
                d = Database ( dbname, progressbar=True, force_load = force_load )
                txnd = d.getExpResults()[0].datasets[0].txnameList[0].txnameData
                if hasattr ( txnd, "origdata" ):
                    print ( "[publishDatabasePickle] FATAL: we still have orig data!" )
                    sys.exit()


        dbver = d.databaseVersion
        picklefile = os.path.join ( dbname, d.txt_meta.getPickleFileName() )

    if args.remove_superseded:
        # e = copy.deepcopy( d )
        e = Database ( picklefile, progressbar=True )
        e2 = removeSupersededFromDB ( e, invert=True, outfile="superseded.pcl" )
        print ( "[publishDatabasePickle] superseded database is called", e.databaseVersion )
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
        e.subs[0].databaseVersion="fastlim"+dbver
    if args.remove_nonaggregated:
        # e = copy.deepcopy( d )
        e = Database ( picklefile, progressbar=True )
        ## create fastlim only
        e = removeNonAggregatedFromDB ( e, invert = True, picklefile = "nonaggregated.pcl" )
        d = removeNonAggregatedFromDB ( d, picklefile = "official.pcl" )
        d.pcl_meta.hasFastLim = False
        d.txt_meta.hasFastLim = False
        d.subs[0].databaseVersion = dbver # .replace("fastlim","official")
        e.subs[0].databaseVersion="nonaggregated"+dbver
    if args.full_llhds:
        f = Database ( picklefile, progressbar=True )
        f = selectFullLikelihoodsFromDB ( f, picklefile = "full_llhds.pcl" )
        f.subs[0].databaseVersion=dbver
        # print ( f"[publishDatabasePickle] dbver {dbver} ver {f.databaseVersion}" )

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
    print ( f"[publishDatabasePickle] {meta}" )
    ver = meta.databaseVersion.replace(".","")
    sfastlim=""
    if fastlim:
        sfastlim="_fastlim"

    infofile = "official%s%s" % ( ver, sfastlim )
    pclfilename = "official%s%s.pcl" % ( ver, sfastlim )
    if args.txnamevalues:
        d.subs[0].databaseVersion="debug"+dbver
        infofile = "debug%s" % ( ver.replace("debug","") )
        pclfilename = "debug%s.pcl" % ( ver.replace("debug","") )
    if "nonaggregated" in ver:
        infofile = "nonaggregated%s" % ( ver.replace("nonaggregated","") )
        pclfilename = "nonaggregated%s.pcl" % ( ver.replace("nonaggregated","") )
    if "full_llhds" in ver:
        infofile = "full_llhds%s" % ( ver.replace("full_llhds","") )
        pclfilename = "full_llhds%s.pcl" % ( ver.replace("full_llhds","") )
    if "superseded" in ver:
        infofile = "superseded%s" % ( ver.replace("superseded","") )
        pclfilename = "superseded%s.pcl" % ( ver.replace("superseded","") )
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
    print ( f"[publishDatabasePickle] writing {pclfilename}" )
    d.createBinaryFile ( pclfilename )
    print ( "[publishDatabasePickle] database size", sizeof_fmt ( os.stat(pclfilename).st_size ) )
    createInfoFile ( infofile, pclfilename, meta.mtime )
    if has_nonValidated:
        nvlist = ",".join(which)
        if args.ignore:
            print ( f"has non-validated results ({nvlist}), but you requested to continue." )
        else:
            print ( f"has non-validated results ({nvlist}). Stopping the procedure." )
            sys.exit()
    sexec="executing:"
    if args.dry_run:
        sexec="suppressing execution of:"
    if not ssh:
        print ( "eos exists on this machine! copy file!" )
        cmd = "cp %s %s/" % ( pcfilename, eosdir )
        a=CMD.getoutput ( cmd )
        if len(a)>0:
            print ( "[publishDatabasePickle] %s" % a )
    cmd = "mv %s ../../smodels.github.io/database/%s" % ( infofile, infofile )
    print ( "[publishDatabasePickle] %s %s" % ( sexec, cmd ) )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )

    if args.latest:
        latestfile = "latest"
        if not args.remove_fastlim:
            latestfile = "latest_fastlim"
        cmd = "cp ../../smodels.github.io/database/%s ../../smodels.github.io/database/%s" %\
               ( infofile, latestfile )
        if not args.dry_run:
            a=CMD.getoutput ( cmd )
            print ( "[publishDatabasePickle] update latest:", cmd, a )
    backupfile = None
    if not args.txnamevalues and not "superseded" in ver and not "full_llhds" in ver and not "nonaggregated" in ver and not "fastlim" in ver: # build the backup version
        backupfile = "backup"+ver
        #if not args.remove_fastlim:
        #    backupfile = "backup_fastlim"
        cmd = "cp ../../smodels.github.io/database/%s ../../smodels.github.io/database/%s" %\
               ( infofile, backupfile )
        if not args.dry_run:
            a=CMD.getoutput ( cmd )
            print ( "[publishDatabasePickle] update backup:", cmd, a )
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
    hasSSHpass = (shutil.which("sshpass")!=None)
    if ssh and not args.dry_run:
        cmd2 = f"scp {pclfilename} lxplus.cern.ch:{eosdir}{pclfilename}"
        if hasSSHpass:
            cmd2 = f"sshpass -f {home}/.ssh/lxplus {cmd2}"
        print ( "%s[publishDatabasePickle] Now please execute manually (and I copied command to your clipboard):%s" % ( ansi.RED, ansi.RESET ) )
        print ( cmd2 )
        reallyDo = not args.dry_run
        if reallyDo:
            o = CMD.getoutput ( cmd2 )
            print ( f"[publishDatabasePickle] {cmd2}: {o}" )
        addToCommandsFile ( cmd2 )
        o = CMD.getoutput ( "echo '%s' | xsel -i" % cmd2 )
        if not reallyDo:
            print ( "[publishDatabasePickle] NOT done (because commands.sh):", cmd2 )
        print ( )
        # print ( "[publishDatabasePickle] (have to do this by hand, if no password-less ssh is configured)" )
        #print ( "%s[publishDatabasePickle] then do also manually:%s" % \
        #        ( ansi.RED, ansi.RESET ) )
        cmd = f"ssh lxplus.cern.ch smodels/www/database/create.py"
        if hasSSHpass:
            cmd = f"sshpass -f {home}/.ssh/lxplus {cmd}"
        CMD.getoutput ( cmd )
        print ( "[publishDatabasePickle] done:", cmd )
        if args.finalize_commands:
            addToCommandsFile ( cmd )
        print ( )
        print ( "now point your browser to: " )
        print ( "https://smodels.web.cern.ch/smodels/database/" )

main()

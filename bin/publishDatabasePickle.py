#!/usr/bin/env python3

""" makes a database pickle file publically available.
The script is deliberately run with python2. That way we get
a pickle file that should work with both python2 and python3. """

from __future__ import print_function
import pickle, os, sys, argparse, time, copy
from smodels.experiment.databaseObj import Database
from smodels_utils.helper.databaseManipulations import \
    removeFastLimFromDB, removeSupersededFromDB
import hashlib
import pathlib
import colorama
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
                print ( "[publishDatabasePickle] %sNon-validated result: %s%s, %s, %s: %s " % \
                        ( colorama.Fore.RED, e.globalInfo.id, colorama.Fore.RESET, \
                          ds, tx, tx.validated) )
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
    has_nonValidated = False
    nonValidated = []
    discard_zeroes=True
    if "test" in dbname:
        discard_zeroes = False
    fastlim = True
    picklefile = dbname
    if not args.build:
        d = Database ( dbname, discard_zeroes=discard_zeroes )
    if args.build:
        if not os.path.isdir ( dbname ):
            print ( "supplied --build option, but %s is not a directory." % dbname )
            sys.exit()
        if args.txnamevalues:
            print ( "[publishDatabasePickle] building with txname values!" )
            import smodels.experiment.txnameObj
            smodels.experiment.txnameObj.TxNameData._keep_values = True
        import smodels
        print ( "[publishDatabasePickle] building database ''%s'' with ''%s''" % \
                (dbname, os.path.dirname ( smodels.__file__ ) ) )
        d = Database ( dbname, discard_zeroes=discard_zeroes, progressbar=True )
        dbver = d.databaseVersion
        if args.remove_superseded:
            # e = copy.deepcopy( d )
            e = Database ( dbname, discard_zeroes=discard_zeroes, progressbar=True )
            e2 = removeSupersededFromDB ( e, invert=True, outfile="superseded.pcl" )
            print ( "[publishDatabasePickle] superseded database is called", e.databaseVersion )
            d = removeSupersededFromDB ( d )
        if args.remove_fastlim:
            # e = copy.deepcopy( d )
            e = Database ( dbname, discard_zeroes=discard_zeroes, progressbar=True )
            ## create fastlim only
            e = removeFastLimFromDB ( e, invert = True, picklefile = "fastlim.pcl" )
            d = removeFastLimFromDB ( d, picklefile = "official.pcl" )
            d.pcl_meta.hasFastLim = False
            d.txt_meta.hasFastLim = False
            d.subs[0].databaseVersion = dbver # .replace("fastlim","official")
            e.subs[0].databaseVersion="fastlim"+dbver
        if not args.skipValidation:
            validated, which = checkNonValidated(d)
            has_nonValidated = validated
        else:
            has_nonValidated = False
        picklefile = os.path.join ( dbname, d.txt_meta.getPickleFileName() )

    p=open(picklefile,"rb")
    meta=pickle.load(p)
    fastlim = meta.hasFastLim
    if args.remove_fastlim:
        fastlim = False
    print ( meta )
    ver = meta.databaseVersion.replace(".","")
    p.close()
    sfastlim=""
    if fastlim:
        sfastlim="_fastlim"

    infofile = "official%s%s" % ( ver, sfastlim )
    pclfilename = "official%s%s.pcl" % ( ver, sfastlim )
    if "superseded" in ver:
        infofile = "superseded%s%s" % ( ver.replace("superseded",""), sfastlim )
        pclfilename = "superseded%s%s.pcl" % ( ver.replace("superseded",""), sfastlim )
    if "fastlim" in ver:
        infofile = "fastlim%s%s" % ( ver.replace("fastlim",""), sfastlim )
        pclfilename = "fastlim%s%s.pcl" % ( ver.replace("fastlim",""), sfastlim )

    if ver == "unittest":
        smodels_ver = "112"
        infofile = "unittest%s" % smodels_ver
        pclfilename = "%s.pcl" % infofile
    else:
        if "unittest" in ver:
            smodels_ver = ver.replace("unittest","")
            infofile = "unittest%s" % smodels_ver
            pclfilename = "%s.pcl" % infofile

    #cmd = "cp %s ./%s" % ( picklefile, pclfilename )
    ssh = True
    if os.path.exists ( eosdir ): ## eos exists locally? copy!
        ssh = False
    print ( f"[publishDatabasePickle] writing {pclfilename}" )
    d.createBinaryFile ( pclfilename )
    print ( "[publishDatabasePickle] database size", sizeof_fmt ( os.stat(pclfilename).st_size ) )
    f=open ( infofile, "w" )
    mtime = time.asctime(time.localtime(meta.mtime))
    sha = _getSHA1 ( pclfilename )
    Dict = { "lastchanged": meta.mtime, "mtime": mtime, "size": os.stat(pclfilename).st_size,
             "url": "https://smodels.web.cern.ch/smodels/database/%s" % pclfilename,
             "sha1": sha }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    if has_nonValidated:
        nvlist = ",".join(which)
        if args.ignore:
            print ( "has non-validated results (%s), but you requested to continue." % nvlist )
        else:
            print ( "has non-validated results (%s). Stopping the procedure." % nvlist )
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
    cmd = f"cd ../../smodels.github.io/; git pull; git add database/{infofile}; "  
    if args.latest:
        cmd += f"git add database/{latestfile}; "
    cmd += "git commit -m 'auto-commited by publishDatabasePickle.py'; git push"
    if args.dry_run:
        print ( f"suppressing execution of: {cmd}" )
    else:
        a=CMD.getoutput ( cmd )
        print ( a )
        
    home = os.environ["HOME"]
    if ssh:
        cmd2 = "sshpass -f %s/.ssh/lxplus scp %s lxplus.cern.ch:%s%s" % \
                ( home, pclfilename, eosdir, pclfilename )
        print ( "%s[publishDatabasePickle] Now please execute manually (and I copied command to your clipboard):%s" % ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "cmd", cmd2 )
        # o = CMD.getoutput ( cmd2 )
        print ( "[publishDatabasePickle] done:", cmd2 )
        addToCommandsFile ( cmd2 )
        CMD.getoutput ( "echo '%s' | xsel -i" % cmd2 )
        print ( )
        # print ( "[publishDatabasePickle] (have to do this by hand, if no password-less ssh is configured)" )
        #print ( "%s[publishDatabasePickle] then do also manually:%s" % \
        #        ( colorama.Fore.RED, colorama.Fore.RESET ) )
        cmd = f"sshpass -f {home}/.ssh/lxplus ssh lxplus.cern.ch smodels/www/database/create.py"
        CMD.getoutput ( cmd )
        print ( "[publishDatabasePickle] done:", cmd )
        if args.finalize_commands:
            addToCommandsFile ( cmd )
        print ( )
        print ( "now point your browser to: " )
        print ( "https://smodels.web.cern.ch/smodels/database/" )

main()

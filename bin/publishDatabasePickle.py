#!/usr/bin/env python3

""" makes a database pickle file publically available.
The script is deliberately run with python2. That way we get
a pickle file that should work with both python2 and python3. """

from __future__ import print_function
import pickle, os, sys, argparse, time
from smodels.experiment.databaseObj import Database
import smodels
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
                print ( "Non-validated result: %s,%s, %s: %s " % \
                        ( e.globalInfo.id, ds, tx, tx.validated) )
                has_nonValidated = True
                nonValidateds.add ( e.globalInfo.id )
    return has_nonValidated, nonValidateds

def removeSuperseded ( db ):
    """ remove superseded results """
    print ( "[publishDatabasePickle] before removal of superseded",len(db.expResultList),"results" )
    filteredList = []
    ctr = 0
    superseded, supers, newers = [], [], []
    olders = db.expResultList
    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersedes" ):
            superseded.append ( gI.supersedes )
    for er in olders:
        gI = er.globalInfo
        if hasattr ( gI, "supersededBy" ): # or gI.id in superseded:
            newers.append ( er )
        else:
            supers.append ( er )
    db.subs[0].expResultList = supers
    db.subs = [ db.subs[0] ]
    print ( "[publishDatabasePickle] after removal of superseded",len(db.expResultList),"results" )
    db.createBinaryFile( "temp.pcl" )
    return db


def removeFastLim ( db ):
    """ remove fastlim results """
    print ( "[publishDatabasePickle] before removal of fastlim",len(db.expResultList),"results" )
    filteredList = []
    ctr = 0
    for e in db.expResultList:
        gI = e.globalInfo
        if hasattr ( gI, "contact" ) and "fastlim" in gI.contact.lower():
            ctr+=1
            if ctr < 4:
                print ( "removing", gI.id )
        else:

            filteredList.append ( e )
    if ctr > 3:
        print ( f"(removed a total of {ctr} ... )" )
    db.subs[0].expResultList = filteredList
    db.subs = [ db.subs[0] ]
    print ( "[publishDatabasePickle] after removal of fastlim",len(db.expResultList),"results" )
    db.txt_meta.hasFastLim = False
    db.createBinaryFile( "temp.pcl" )
    db.subs[0].pcl_meta.hasFastLim = False
    return db

def main():
    ap = argparse.ArgumentParser( description="makes a database pickle file publically available (run it on the smodels)" )
    ap.add_argument('-f', '--filename', help='name of pickle file [database.pcl]', default="database.pcl" )
    ap.add_argument('-d', '--dry_run', help='dont copy to final destination', action="store_true" )
    ap.add_argument('-l', '--latest', help='define as latest database', action="store_true" )
    ap.add_argument('-b', '--build', help='build pickle file, assume filename is directory name', action="store_true" )
    ap.add_argument('-r', '--remove_fastlim', help='build pickle file, remove fastlim results', action="store_true" )
    ap.add_argument('-s', '--remove_superseded', help='build pickle file, remove superseded results', action="store_true" )
    ap.add_argument('-P', '--smodelsPath', help='path to the SModelS folder [None]', default=None )
    ap.add_argument('-V', '--skipValidation', help='if set will skip the check of validation flags [False]', default=False, action="store_true" )
    args = ap.parse_args()
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
        print ( "[publishDatabasePickle] building database with %s" % os.path.dirname ( smodels.__file__ ) )
        d = Database ( dbname, discard_zeroes=discard_zeroes )
        if args.remove_superseded:
            d = removeSuperseded ( d )
        if args.remove_fastlim:
            d = removeFastLim ( d )
            d.pcl_meta.hasFastLim = False
            d.txt_meta.hasFastLim = False
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
    if not args.dry_run:
        d.createBinaryFile ( pclfilename )
    #if not args.dry_run and not args.build:
    #    print ( "[publishDatabasePickle] %s" % cmd )
    #    a=CMD.getoutput ( cmd )
    #    print ( "[publishDatabasePickle] %s" % a )
    print ( "[publishDatabasePickle] database size", sizeof_fmt ( os.stat(pclfilename).st_size ) )
    f=open ( infofile, "w" )
    mtime = time.asctime(time.localtime(meta.mtime))
    Dict = { "lastchanged": meta.mtime, "mtime": mtime, "size": os.stat(pclfilename).st_size,
             "url": "https://smodels.web.cern.ch/smodels/database/%s" % pclfilename }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    if has_nonValidated:
        nvlist = ",".join(which)
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
        
    if ssh:
        cmd2 = "scp %s lxplus.cern.ch:%s%s" % ( pclfilename, eosdir, pclfilename )
        print ( "%s[publishDatabasePickle] Now please execute manually (and I copied command to your clipboard):%s" % ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( cmd2 )
        CMD.getoutput ( "echo '%s' | xsel -i" % cmd2 )
        print ( )
        print ( "[publishDatabasePickle] (have to do this by hand, if no password-less ssh is configured)" )
        print ( "%s[publishDatabasePickle] then do also manually:%s" % ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "ssh lxplus.cern.ch smodels/www/database/create.py" )
        print ( )
        print ( "now point your browser to: " )
        print ( "https://smodels.web.cern.ch/smodels/database/" )

main()

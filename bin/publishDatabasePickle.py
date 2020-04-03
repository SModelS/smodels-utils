#!/usr/bin/env python3

""" makes a database pickle file publically available.
The script is deliberately run with python2. That way we get
a pickle file that should work with both python2 and python3. """

from __future__ import print_function
import pickle, os, sys, argparse, time
import colorama
if sys.version[0]=="2":
    import commands as CMD
else:
    print ( "you sure you want to run this with python3?" )
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
    for e in expResults:
        for ds in e.datasets:
            for tx in ds.txnameList:
                if tx.validated in [ False, True, "N/A", "n/a" ]:
                    continue
                print ( "Non-validated result: %s,%s, %s: %s " % \
                        ( e.globalInfo.id, ds, tx, tx.validated) )
                has_nonValidated = True
    return has_nonValidated

def removeFastLim ( db ):
    """ remove fastlim results """
    print ( "before removal",len(db.getExpResults()),"results" )
    filteredList = []
    ctr = 0
    for e in db.getExpResults():
        gI = e.globalInfo
        if hasattr ( gI, "contact" ) and "fastlim" in gI.contact.lower():
            ctr+=1
            if ctr < 4:
                print ( "removing", gI.id )
            if ctr == 4:
                print ( "(removing more ... )" )
        else:

            filteredList.append ( e )
    db.expResultList = filteredList
    print ( "after removal",len(db.getExpResults()),"results" )
    db.pcl_meta.hasFastLim = False
    db.txt_meta.hasFastLim = False
    db.createBinaryFile()
    return db

def main():
    ap = argparse.ArgumentParser( description="makes a database pickle file publically available (run it on the smodels)" )
    ap.add_argument('-f', '--filename', help='name of pickle file [database.pcl]', default="database.pcl" )
    ap.add_argument('-d', '--dry_run', help='dont copy to final destination', action="store_true" )
    # ap.add_argument('-l', '--fastlim', help='add fastlim results when pickling', action="store_true" )
    ap.add_argument('-b', '--build', help='build pickle file, assume filename is directory name', action="store_true" )
    ap.add_argument('-r', '--remove_fastlim', help='build pickle file, remove fastlim results', action="store_true" )
    ap.add_argument('-P', '--smodelsPath', help='path to the SModelS folder [None]', default=None )
    ap.add_argument('-V', '--skipValidation', help='if set will skip the check of validation flags [False]', default=False, action="store_true" )
    args = ap.parse_args()
    dbname = args.filename
    if args.smodelsPath:
        sys.path.append(os.path.abspath(args.smodelsPath))
    has_nonValidated = False
    discard_zeroes=True
    if "test" in dbname:
        discard_zeroes = False
    fastlim = True
    if args.build:
        if not os.path.isdir ( dbname ):
            print ( "supplied --build option, but %s is not a directory." % dbname )
            sys.exit()
        import smodels
        print ( "[publishDatabasePickle] building database with %s" % os.path.dirname ( smodels.__file__ ) )
        from smodels.experiment.databaseObj import Database
        d = Database ( dbname, discard_zeroes=discard_zeroes )
        if args.remove_fastlim:
            d = removeFastLim ( d )
            d.pcl_meta.hasFastLim = False
            d.txt_meta.hasFastLim = False
        dbname = d.pcl_meta.pathname
        if not args.skipValidation:
            has_nonValidated = checkNonValidated(d)
        else:
            has_nonValidated = False
        fastlim = d.pcl_meta.hasFastLim

    p=open(dbname,"rb")
    meta=pickle.load(p)
    fastlim = meta.hasFastLim
    print ( meta )
    print ( "[publishDatabasePickle] database size", sizeof_fmt ( os.stat(dbname).st_size ) )
    ver = meta.databaseVersion.replace(".","")
    p.close()
    sfastlim=""
    if fastlim:
        sfastlim="_fastlim"
    infofile = "official%s%s" % ( ver, sfastlim )
    pclfilename = "official%s%s.pcl" % ( ver, sfastlim )
    if ver == "unittest":
        smodels_ver = "112"
        infofile = "unittest%s" % smodels_ver
        pclfilename = "%s.pcl" % infofile
    else:
        if "unittest" in ver:
            smodels_ver = ver.replace("unittest","")
            infofile = "unittest%s" % smodels_ver
            pclfilename = "%s.pcl" % infofile

    f=open ( infofile, "w" )
    mtime = time.asctime(time.localtime(meta.mtime))
    Dict = { "lastchanged": meta.mtime, "mtime": mtime, "size": os.stat(dbname).st_size,
             "url": "https://smodels.web.cern.ch/smodels/database/%s" % pclfilename }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    if has_nonValidated:
        print ( "has non-validated results. Stopping the procedure." )
        sys.exit()
    cmd = "mv %s ./%s" % ( dbname, pclfilename )
    ssh = True
    if os.path.exists ( eosdir ): ## eos exists locally? copy!
        ssh = False
    if not args.dry_run:
        print ( "[publishDatabasePickle] %s" % cmd )
        a=CMD.getoutput ( cmd )
        print ( "[publishDatabasePickle] %s" % a )
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
    print("\n\t -----> The json file has to be updated in the smodels.github.io:master/database repository.\n")
    print("\n\t -----> The .pcl file can be uploaded through https://cernbox.cern.ch/index.php/s/jt7xJCepuXTRWPL\n\n")
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )
    if ssh:
        cmd2 = "scp %s lxplus.cern.ch:%s%s" % ( pclfilename, eosdir, pclfilename )
        print ( "%s[publishDatabasePickle] Now please execute manually:%s" % ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( cmd2 )
        print ( )
        print ( "[publishDatabasePickle] (have to do this by hand, if no password-less ssh is configured)" )
        print ( "%s[publishDatabasePickle] then do also manually:%s" % ( colorama.Fore.RED, colorama.Fore.RESET ) )
        print ( "ssh lxplus.cern.ch smodels/www/database/create.py" )
        print ( )


main()

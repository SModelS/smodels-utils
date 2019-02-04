#!/usr/bin/env python3

""" makes a database pickle file publically available. 
The script is deliberately run with python2. That way we get 
a pickle file that should work with both python2 and python3. """

from __future__ import print_function
import pickle, os, sys, argparse
if sys.version[0]=="2":
    import commands as CMD
else:
    print ( "you sure you want to run this with python3?" )
    import subprocess as CMD

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
    for e in db.getExpResults():
        gI = e.globalInfo
        if hasattr ( gI, "contact" ) and "fastlim" in gI.contact.lower():
            print ( "removing", gI.id )
        else:
                
            filteredList.append ( e )
    db.expResultList = filteredList
    print ( "after removal",len(db.getExpResults()),"results" )
    db.pcl_meta.hasFastLim = False
    db.createBinaryFile()
    return db

def main():
    ap = argparse.ArgumentParser( description="makes a database pickle file publically available (run it on the smodels)" )
    ap.add_argument('-f', '--filename', help='name of pickle file [database.pcl]', default="database.pcl" )
    ap.add_argument('-d', '--dry_run', help='dont copy to final destination', action="store_true" )
    # ap.add_argument('-l', '--fastlim', help='add fastlim results when pickling', action="store_true" )
    ap.add_argument('-b', '--build', help='build pickle file, assume filename is directory name', action="store_true" )
    ap.add_argument('-r', '--remove_fastlim', help='build pickle file, remove fastlim results', action="store_true" )
    ap.add_argument('-s', '--ssh', help='work remotely via ssh', action="store_true" )
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
    print ( "[publishDatabasePickle] database size", os.stat(dbname).st_size )
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
    # Dict = { "lastchanged": meta.mtime, "size": os.stat(dbname).st_size, "url": "http://smodels.hephy.at/database/%s" % pclfilename }
    Dict = { "lastchanged": meta.mtime, "size": os.stat(dbname).st_size, "url": "https://smodels.web.cern.ch/smodels/database/%s" % pclfilename }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    if has_nonValidated:
        print ( "has non-validated results. Stopping the procedure." )
        sys.exit()
    cmd = "cp %s /nfsdata/walten/database/%s" % ( dbname, pclfilename )
    if args.ssh:
        # cmd = "scp %s smodels.hephy.at:/nfsdata/walten/database/%s" % ( dbname, pclfilename )
        cmd = "scp %s lxplus.cern.ch:/eos/project/s/smodels/www/database/%s" % ( dbname, pclfilename )
        # print ( "(might have to do this by hand, if no password-less ssh is configured)" )
    if not args.dry_run:
        print ( "[publishDatabasePickle] %s" % cmd )
        a=CMD.getoutput ( cmd )
        print ( "[publishDatabasePickle] %s" % a )
    symlinkfile = "/var/www/database/%s" % pclfilename 
    cmd = "rm -f %s" % symlinkfile
    if args.ssh:
        cmd = "ssh smodels.hephy.at %s" % cmd
    a = CMD.getoutput ( cmd )
    print ( "[publishDatabasePickle] %s" % a )
    sexec="executing:"
    if args.dry_run:
        sexec="suppressing execution of:"
    ## not needed at CERN server
    """
    cmd = "ln -s /nfsdata/walten/database/%s %s" % ( pclfilename, symlinkfile )
    if args.ssh:
        cmd = "ssh smodels.hephy.at ln -s /nfsdata/walten/database/%s /var/www/database/" % ( pclfilename )
    print ( "[publishDatabasePickle] %s %s" % ( sexec, cmd ) )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )
    """
    # cmd = "cp %s /var/www/database/%s" % ( infofile, infofile )
    cmd = "cp %s ../../smodels.github.io/database/%s" % ( infofile, infofile )
    if args.ssh:
        pass
        # cmd = "scp %s smodels.hephy.at:/var/www/database/%s" % ( infofile, infofile )
    print ( "[publishDatabasePickle] %s %s" % ( sexec, cmd ) )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )

main()

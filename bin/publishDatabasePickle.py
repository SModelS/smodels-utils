#!/usr/bin/env python3

""" makes a database pickle file publically available 
    (script needs to be run on the smodels server) """

from __future__ import print_function
import pickle, os, sys, argparse
if sys.version[0]=="2":
    import commands as CMD
else:
    import subprocess as CMD


def main():
    ap = argparse.ArgumentParser( description="makes a database pickle file publically available (run it on the smodels)" )
    ap.add_argument('-f', '--filename', help='name of pickle file', default="database.pcl" )
    ap.add_argument('-d', '--dry_run', help='dont copy to final destination', action="store_true" )
    ap.add_argument('-b', '--build', help='build pickle file, assume filename is directory name', action="store_true" )
    ap.add_argument('-s', '--ssh', help='work remotely via ssh', action="store_true" )
    ap.add_argument('-P', '--smodelsPath', help='path to the SModelS folder', default=None )
    args = ap.parse_args()
    dbname = args.filename
    if args.smodelsPath:
        sys.path.append(os.path.abspath(args.smodelsPath))
    if args.build:
        if not os.path.isdir ( dbname ):
            print ( "supplied --build option, but %s is not a directory." % dbname )
            sys.exit()
        from smodels.experiment.databaseObj import Database
        d = Database ( dbname )
        dbname = d.pcl_meta.pathname

    p=open(dbname,"rb")
    meta=pickle.load(p)
    print ( meta )
    ver = meta.databaseVersion.replace(".","") 
    p.close()
    infofile = "official%s" % ver 
    pclfilename = "official%s.pcl" % ver
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
    Dict = { "lastchanged": meta.mtime, "size": os.stat(dbname).st_size, "url": "http://smodels.hephy.at/database/%s" % pclfilename }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    cmd = "cp %s /nfsdata/walten/database/%s" % ( dbname, pclfilename )
    if args.ssh:
        cmd = "scp %s smodels.hephy.at:/nfsdata/walten/database/%s" % ( dbname, pclfilename )
    print ( cmd )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )
    cmd = "ln -s /nfsdata/walten/database/%s /var/www/database/" % ( pclfilename )
    if args.ssh:
        cmd = "ssh smodels.hephy.at ln -s /nfsdata/walten/database/%s /var/www/database/" % ( pclfilename )
    print ( cmd )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )
    cmd = "cp %s /var/www/database/%s" % ( infofile, infofile )
    if args.ssh:
        cmd = "scp %s smodels.hephy.at:/var/www/database/%s" % ( infofile, infofile )
    print ( cmd )
    if not args.dry_run:
        a=CMD.getoutput ( cmd )
        print ( a )

main()

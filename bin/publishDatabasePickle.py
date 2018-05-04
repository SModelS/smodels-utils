#!/usr/bin/python

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
    ap.add_argument('-s', '--ssh', help='work remotely via ssh', action="store_true" )
    args = ap.parse_args()
    p=open(args.filename,"rb")
    meta=pickle.load(p)
    print ( meta )
    ver = meta.databaseVersion.replace(".","") 
    p.close()
    infofile = "official%s" % ver 
    pclfilename = "off%s.pcl" % ver
    if ver == "unittest":
        smodels_ver = "112"
        infofile = "unittest%s" % smodels_ver
        pclfilename = "%s.pcl" % infofile
    f=open ( infofile, "w" )
    Dict = { "lastchanged": meta.mtime, "size": os.stat(args.filename).st_size, "url": "http://smodels.hephy.at/database/%s" % pclfilename }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    cmd = "cp %s /nfsdata/walten/database/%s" % ( args.filename, pclfilename )
    if args.ssh:
        cmd = "scp %s smodels.hephy.at:/nfsdata/walten/database/%s" % ( args.filename, pclfilename )
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

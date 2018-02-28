#!/usr/bin/python

""" makes a database pickle file publically available 
    (script needs to be run on the smodels server) """

from __future__ import print_function
import pickle, commands, os, sys, argparse

def main():
    ap = argparse.ArgumentParser( description="makes a database pickle file publically available (run it on the smodels)" )
    ap.add_argument('-f', '--filename', help='name of pickle file', default="database.pcl" )
    ap.add_argument('-d', '--dry_run', help='dont copy to final destionation', action="store_true" )
    args = ap.parse_args()
    p=open(args.filename)
    meta=pickle.load(p)
    print ( "meta: %s" % meta )
    ver = meta.databaseVersion.replace(".","") 
    p.close()
    infofile = "official%s" % ver 
    f=open ( infofile, "w" )
    Dict = { "lastchanged": meta.mtime, "size": os.stat(args.filename).st_size, "url": "http://smodels.hephy.at/database/off%s.pcl" % ver }
    f.write ( "%s\n" % str(Dict).replace ( "'", '"' ) )
    f.close()
    # cmd = "cp %s /var/www/database/off%s.pcl" % ( args.filename, ver )
    cmd = "cp %s /nfsdata/walten/database/off%s.pcl" % ( args.filename, ver )
    print ( cmd )
    if not args.dry_run:
        a=commands.getoutput ( cmd )
        print ( a )
    cmd = "ln -s /nfsdata/walten/database/off%s.pcl /var/www/database/" % ( ver )
    print ( cmd )
    if not args.dry_run:
        a=commands.getoutput ( cmd )
        print ( a )
    cmd = "cp %s /var/www/database/official%s" % ( infofile, ver )
    print ( cmd )
    if not args.dry_run:
        a=commands.getoutput ( cmd )
        print ( a )

main()

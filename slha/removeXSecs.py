#!/usr/bin/env python3

""" remove all cross sections from files """

import subprocess, sys

def removeEmptyLines ( fl ):
    """ remove empty lines """
    f = open ( fl, "rt" )
    lines = f.readlines()
    f.close()
    g = open ( fl, "wt" )
    isInXsec = False
    for line in lines:
        if isInXsec and line.strip() == "":
            continue
        if line.strip() == "":
            isInXsec = True
        else:
            isInXsec = False
        g.write ( line )
    f.close()

def getSqrtsString ( sqrts ):
    """ construct a string that I can grep for """
    if sqrts == 0:
        return ""
    if sqrts == 8:
        return "8.00E+03"
    if sqrts == 13:
        return "1.30E+04"
    print ( f"[removeXSecs] sqrts is {sqrts}, dont know how to handle" )
    return None

def removeForPid ( fl, pid, sqrts, pid2 ):
    """ remove only for a single pid and sqrts """
    f = open ( fl, "rt" )
    lines = f.readlines()
    f.close()
    g = open ( fl, "wt" )
    isInXsec = False
    spid2 = ""
    if pid2 != 0:
        spid2 = f" {str(pid2)}"
    for line in lines:
        p1 = line.find ( " "+str(pid) )
        p2 = line.find ( spid2 )
        if "XSECTION" in line and " "+str(pid) in line and getSqrtsString ( sqrts ) in line and spid2 in line and p2 != p1:
            isInXsec = True
            continue
        if isInXsec == True:
            isInXsec = False
            continue
        g.write ( line )
    f.close()

def removeAll ( fl, sqrts ):
    """ remove all xsecs, if sqrts is not zero, then remove all of a certain sqrts """
    print ( f"cleaning {fl}" )
    f = open ( fl, "rt" )
    lines = f.readlines()
    f.close()
    g = open ( fl, "wt" )
    for line in lines:
        if "Signal strength" in line:
            continue
        if "XSECTION" in line and getSqrtsString ( sqrts ) in line:
            break
        g.write ( line )

def zipThem ( files ):
    """ zip them up """
    topo = files[0][:files[0].find("_")]
    cmd = f"tar czvf {topo}.tar.gz {topo}*slha"
    print ( cmd )
    subprocess.getoutput ( cmd )
    cmd = f"rm {topo}*slha"
    print ( cmd )
    subprocess.getoutput ( cmd )
    cmd = "rm -r T*slha"
    subprocess.getoutput ( cmd )

def main():
    import glob, argparse
    argparser = argparse.ArgumentParser(description="remove xsecs from slha files" )
    argparser.add_argument ( '-p', '--pid', nargs='?', 
                    help='remove xsecs only for pid, if zero remove for all [0]',
                    type=int, default=0 )
    argparser.add_argument('-f', '--files', 
                           help = 'file pattern to glob, if tarball given, then unpack [T*.slha]',
                           type=str,default = "T*.slha" )
    argparser.add_argument ( '-q', '--pid2', nargs='?', 
                    help='remove xsecs only for pid/pid2, if zero, ignore [0]',
                    type=int, default=0 )
    argparser.add_argument ( '-s', '--sqrts', nargs='?', 
                    help='remove xsecs only for certain sqrts, if zero remove for all [0]',
                    type=int, default=0 )
    argparser.add_argument ( '-c', '--clean', action="store_true",  
                    help="remove subsequent empty newlines" )
    argparser.add_argument('-z', '--zip', help="zip them up at the end",
                            action = "store_true" )
    args=argparser.parse_args()
    if args.files.endswith(".tar.gz"):
        files = glob.glob("T*slha")
        if len(files)>0:
            print ( "[addRefXSecs] error, you ask me to unpack a tarball but there are slha files in the directory." )
            sys.exit()
        ## remove cruft slha files, unpack tarball
        cmd = "rm -rf T*slha" 
        subprocess.getoutput ( cmd )
        cmd = f"tar xzvf {args.files}"
        subprocess.getoutput ( cmd )
        args.files = "T*slha"
    files = glob.glob( args.files )
    for fl in files:
        if args.clean:
            removeEmptyLines ( fl )
        if args.pid == 0:
            removeAll ( fl, args.sqrts )
        else:
            removeForPid ( fl, args.pid, args.sqrts, args.pid2 )
    if args.zip:
        zipThem ( files )

main()

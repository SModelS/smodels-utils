#!/usr/bin/env python3

""" remove all cross sections from files """

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

def removeForPid ( fl, pid ):
    """ remove only for a single pid """
    f = open ( fl, "rt" )
    lines = f.readlines()
    f.close()
    g = open ( fl, "wt" )
    isInXsec = False
    for line in lines:
        if "XSECTION" in line and str(pid) in line:
            isInXsec = True
            continue
        if isInXsec == True:
            isInXsec = False
            continue
        g.write ( line )
    f.close()

def removeAll ( fl ):
    """ remove all xsecs """
    print ( "cleaning %s" % fl )
    f = open ( fl, "rt" )
    lines = f.readlines()
    f.close()
    g = open ( fl, "wt" )
    for line in lines:
        if "Signal strength" in line:
            continue
        if "XSECTION" in line:
            break
        g.write ( line )

def main():
    import glob, argparse
    argparser = argparse.ArgumentParser(description="remove xsecs from slha files" )
    argparser.add_argument ( '-p', '--pid', nargs='?', 
                    help='remove xsecs only for pid, if zero remove for all [0]',
                    type=int, default=0 )
    argparser.add_argument ( '-c', '--clean', action="store_true",  
                    help="remove subsequent empty newlines" )
    args=argparser.parse_args()
    files = glob.glob("*.slha" )
    for fl in files:
        if args.clean:
            removeEmptyLines ( fl )
        if args.pid == 0:
            removeAll ( fl )
        else:
            removeForPid ( fl, args.pid )

main()

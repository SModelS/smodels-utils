#!/usr/bin/env python3

""" python script to add the reference cross sections to slha files.
The cross sections have been scraped off from 
https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections
and stored in the xsec*.txt files. """

import os, subprocess, sys

def addToFile ( F, pid1, pid2, xsecs, sqrts, dry_run, order ):
    """ add to file F cross sections for pid1, pid2 
    :param order: perturbation order that we should claim this to be
                  (LO=0, NLO=1, NLL=2, ... )
    """
    tokens = F.split("_")
    mass = float(tokens[1])
    xsec = interpolate ( mass, xsecs )
    if xsec == None:
        print ( "[addRefXSecs] skipping %d" % mass )
        return
    # print ( "[addRefXSecs] adding %d/%d:%.4f to %s" % ( pid1, pid2, xsec, F ) )
    f=open(F,"rt")
    lines=f.readlines()
    f.close()
    if dry_run:
        return
    cmd = "cp %s /tmp/old%s" % ( F, F )
    subprocess.getoutput ( cmd )
    f=open( F, "wt" )
    isInXSec=False
    ssqrt = "%1.3G" % (sqrts*1000)
    ssqrt = ssqrt.replace("E","0E")
    for line in lines:
        if "XSECTION" in line and " "+str(pid1) in line and " "+str(pid2) in line and ssqrt in line:
            #f.write ( "# %s ## replaced\n" % line.strip() )
            isInXSec=True
            continue
        if isInXSec:
            #f.write ( "# %s ## replaced\n" % line.strip() )
            isInXSec=False
            continue
        f.write ( line )
    f.write ( "XSECTION  %s  2212 2212 2 %d %d # reference cross section [pb]\n" % \
              ( ssqrt, pid1, pid2 ) )
    f.write ( "  0  %d  0  0  0  0    %.6G AddRefXSecsv1.0\n" % ( order, xsec ) )
    f.write ( "\n" )
    f.close()

def clean ( F ):
    """ clean up F, if needed. remove double newlines, and ssm line """
    f=open(F,"rt")
    lines=f.readlines()
    f.close()
    f=open(F,"wt")
    newline = False
    for line in lines:
        if "Signal strength multipliers" in line:
            continue
        if newline and line == "\n":
            continue
        if line == "\n":
            newline = True
        else:
            newline = False
        f.write ( line )
    f.close()

def interpolate ( mass, xsecs ):
    """ interpolate between masses """
    if mass in xsecs:
        return xsecs[mass]
    if mass < min(xsecs.keys()):
        print ( "[addRefXSecs] mass %d<%d too low to interpolate, leave it as is."  % ( mass, min(xsecs.keys() ) ) )
        return None
    if mass > max(xsecs.keys()):
        print ( "[addRefXSecs] mass %d>%d too high to interpolate, leave it as is." % ( mass, max(xsecs.keys() ) ) )
        return None
    from scipy.interpolate import interp1d
    return interp1d ( list(xsecs.keys()), list(xsecs.values()) )( mass )

def getXSecsFrom ( filename, pb = True, columns={"mass":0,"xsec":1 } ):
    """ retrieve xsecs from filename
    :param pb: xsecs given in pb
    :param indices: the indices of the columns in the table, for mass and xsec
    """
    ret = {}
    if not os.path.exists ( filename ):
        print ( "[addRefXSecs] could not find %s" % filename )
        return ret
    print ( "getting xsecs from %s" % filename )
    f = open ( filename, "rt" )
    lines=f.readlines()
    f.close()
    for line in lines:
        if line.find("#")>-1:
            line = line[:line.find("#")]
        if "mass [GeV]" in line: ## skip
            continue
        tokens = line.split ()
        if len(tokens)<2:
            continue
        mass = float(tokens[ columns["mass"] ])
        xsec = float(tokens[ columns["xsec"] ].replace("GeV","") )
        if not pb:
            xsec = xsec / 1000.
        ret[ mass ] = xsec
    return ret

def getXSecsFor ( pid1, pid2, sqrts ):
    """ get the xsec dictionary for pid1/pid2, sqrts """
    filename=None
    order = 0
    pb = True
    columns = { "mass": 0, "xsec": 1 }
    if pid1 in [ 1000021 ] and pid2 == pid1:
        filename = "xsecgluino%d.txt" % sqrts
        columns["xsec"]=2
        order = 2 # 4
    if pid1 in [ -1000024 ] and pid2 in [ 1000023 ]:
        filename = "xsecN2C1m13.txt"
        order = 2
        pb = False
    if pid1 in [ 1000023 ] and pid2 in [ 1000024 ]:
        filename = "xsecN2C1p13.txt"
        order = 2
        pb = False
    if pid1 in [ 1000024 ] and pid2 in [ 1000025 ]:
        filename = "xsecN2C1p13.txt"
        order = 2
        pb = False
    if pid1 in [ -1000024 ] and pid2 in [ 1000025 ]:
        filename = "xsecN2C1m13.txt"
        order = 2
        pb = False
    if pid1 in [ -1000005, -1000006 ] and pid2 == -pid1:
        ## left handed slep- slep+ production.
        filename = "xsecstop%d.txt" % sqrts
        order = 2 #3
        columns["xsec"]=2
        pb = True
    if pid1 in [ -1000024 ] and pid2 == -pid1:
        ## left handed slep- slep+ production.
        filename = "xsecC1C1%d.txt" % sqrts
        order = 2 #3
        pb = False
    if pid1 in [ -1000011, -1000013, -1000015 ] and pid2 == -pid1:
        ## left handed slep- slep+ production.
        filename = "xsecslepLslepL%d.txt" % sqrts
        order = 2 #3
    if pid1 in [ -2000011, -2000013, -2000015 ] and pid2 == -pid1:
        filename = "xsecslepRslepR%d.txt" % sqrts
        order = 2 # 3
    if filename == None:
        print ( "[addRefXSecs] could not identify filename for xsecs" )
        return {}
    xsecs = getXSecsFrom ( filename, pb, columns )
    return xsecs,order

def zipThem ( files ):
    """ zip them up """
    topo = files[0][:files[0].find("_")]
    cmd = "tar czvf %s.tar.gz %s*slha" % ( topo, topo )
    print ( cmd )
    subprocess.getoutput ( cmd )

def main():
    import argparse, glob
    argparser = argparse.ArgumentParser( description = "add reference cross sections to slha files" )
    argparser.add_argument('-f', '--files', 
                           help = 'file pattern to glob, if tarball given, then unpack [T*.slha]',
                           type=str,default = "T*.slha" )
    argparser.add_argument('-p', '--pid1', help="first particle id [-1000015]",
                           type=int, default = -1000015 )
    argparser.add_argument('-q', '--pid2', help="first particle id [1000015]",
                           type=int, default = 1000015 )
    argparser.add_argument('-s', '--sqrts', help="sqrts [13]",
                           type=int, default = 13 )
    argparser.add_argument('-d', '--dry_run', help="just pretend",
                            action = "store_true" )
    argparser.add_argument('-c', '--clean', help="perform cleanup step",
                            action = "store_true" )
    argparser.add_argument('-z', '--zip', help="zip them up at the end",
                            action = "store_true" )
    args = argparser.parse_args()
    if args.files.endswith(".tar.gz"):
        files = glob.glob("T*slha")
        if len(files)>0:
            print ( "[check_nlo] error, you ask me to unpack a tarball but there are slha files in the directory." )
            sys.exit()
        ## remove cruft slha files, unpack tarball
        cmd = "rm -rf T*slha" 
        subprocess.getoutput ( cmd )
        cmd = "tar xzvf %s" % args.files
        subprocess.getoutput ( cmd )
        args.files = "T*slha"
    files = glob.glob ( args.files )
    if args.pid2 < args.pid1:
        print ( "[addRefXSecs] will swap pids %d and %d" % ( args.pid1, args.pid2) )
        args.pid1, args.pid2 = args.pid2, args.pid1
    xsecs,order = getXSecsFor ( args.pid1, args.pid2, args.sqrts )
    # print ( "xsecs", xsecs )
    for F in files: # [:3]:
        addToFile ( F, args.pid1, args.pid2, xsecs, args.sqrts, args.dry_run, order )
        if args.clean:
            clean ( F )
    if args.zip:
        zipThem ( files )

if __name__ == "__main__":
    main()

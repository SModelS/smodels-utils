#!/usr/bin/env python3

""" python script to add the reference cross sections to slha files.
The cross sections have been scraped off from 
https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SUSYCrossSections
and stored in the xsec*.txt files. """

import os, subprocess, sys
import pyslha

def addToFile ( F, pid1, pid2, xsecs, sqrts, dry_run, order, comment ):
    """ add to file F cross sections for pid1, pid2 
    :param order: perturbation order that we should claim this to be
                  (LO=0, NLO=1, NLL=2, ... )
    :param comment: comment to be added to xsec line
    """
    
    slhaData = pyslha.readSLHAFile(F)    
    tokens = F.split("_")
    mass1 = slhaData.blocks['MASS'][abs(pid1)]
    mass2 = slhaData.blocks['MASS'][abs(pid2)]
    if abs(mass1-mass2) > 1.0:
        print('[addRefXSecs] Can not compute xsecs for pair production of sparticles with distinct masses: %d!=%d' % ( mass1, mass2 ) )
        return
    else:
        mass = (mass1+mass2)/2.
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
    if sqrts > 10:
        ssqrt = ssqrt.replace("E","0E")
    else:
        ssqrt = ssqrt.replace("E",".00E")
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
    f.write ( "\n" )
    f.write ( "XSECTION  %s  2212 2212 2 %d %d # reference cross section [pb]\n" % \
              ( ssqrt, pid1, pid2 ) )
    f.write ( "  0  %d  0  0  0  0    %.6G AddRefXSecsv1.0%s\n" % ( order, xsec, comment ) )
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

def getXSecsFor ( pid1, pid2, sqrts, ewk ):
    """ get the xsec dictionary for pid1/pid2, sqrts 
    :param ewk: specify the ewkino process (hino, or wino)
    """
    filename=None
    order = 0
    pb = True
    columns = { "mass": 0, "xsec": 1 }
    isEWK=False
    comment=""
    if pid1 in [ 1000021 ] and pid2 == pid1:
        filename = "xsecgluino%d.txt" % sqrts
        columns["xsec"]=2
        isEWK=False
        order = 2 # 4
    if pid1 in [ -1000024 ] and pid2 in [ 1000023 ]:
        filename = "xsecN2C1m%d.txt" % sqrts
        order = 2
        isEWK=True
        pb = False
    if pid1 in [ 1000023 ] and pid2 in [ 1000024 ]:
        filename = "xsecN2C1p%d.txt" % sqrts
        order = 2
        pb = False
        isEWK=True
    if pid1 in [ 1000024 ] and pid2 in [ 1000025 ]:
        filename = "xsecN2C1p%d.txt" % sqrts
        order = 2
        pb = False
        isEWK=True
    if pid1 in [ -1000024 ] and pid2 in [ 1000025 ]:
        filename = "xsecN2C1m%d.txt" % sqrts
        order = 2
        isEWK=True
        pb = False
    if pid1 in [ -1000005, -1000006, -2000006 ] and pid2 == -pid1:
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
        print ( "              seems like we dont have ref xsecs for the pids %d/%d?" % ( pid1, pid2 ) )
        sys.exit()
    if ewk == "hino":
        filename = filename.replace(".txt","hino.txt" )
    if isEWK:
        comment = " (%s)" % ewk
    if not os.path.exists ( filename ):
        print ( "[addRefXSecs] %s missing" % filename )
        sys.exit()
    xsecs = getXSecsFrom ( filename, pb, columns )
    return xsecs,order,comment

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
    argparser.add_argument('-e', '--ewk', help="specify the ewkino process, hino or wino [wino]",
                           type=str, default = "wino" )
    argparser.add_argument('-d', '--dry_run', help="just pretend",
                            action = "store_true" )
    argparser.add_argument('-c', '--clean', help="perform cleanup step",
                            action = "store_true" )
    argparser.add_argument('-z', '--zip', help="zip them up at the end",
                            action = "store_true" )
    args = argparser.parse_args()
    if args.ewk not in [ "hino", "wino" ]:
        print ( "[addRefXSecs] error ewk %s not recognised" % args.ewk )
        sys.exit()
    if args.files.endswith(".tar.gz"):
        files = glob.glob("T*slha")
        if len(files)>0:
            print ( "[addRefXSecs] error, you ask me to unpack a tarball but there are slha files in the directory." )
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
    sqrts = [ args.sqrts ]
    if sqrts == [ 0 ]:
        sqrts = [ 8, 13 ]
    for s in sqrts:
        xsecs,order,comment = getXSecsFor ( args.pid1, args.pid2, s, args.ewk )
        # print ( "xsecs", xsecs )
        for F in files: # [:3]:
            addToFile ( F, args.pid1, args.pid2, xsecs, s, args.dry_run, order, comment )
            if args.clean:
                clean ( F )
    if args.zip:
        zipThem ( files )

if __name__ == "__main__":
    main()

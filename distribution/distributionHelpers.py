#!/usr/bin/env python3

"""
.. module:: distributionHelpers
   :synopsis: functions that help with tarball creation

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import colorama, subprocess

RED = "\033[31;11m"
GREEN = "\033[32;11m"
YELLOW = "\033[33;11m"
RESET = "\033[7;0m"
try:
    RED = colorama.Fore.RED
    GREEN = colorama.Fore.GREEN
    YELLOW = colorama.Fore.YELLOW
    RESET = colorama.Fore.RESET
except:
    pass

def runCmd ( cmd : str, prtMsg : bool = True ):
    """ run a certain command """
    cmd=cmd.strip()
    if prtMsg:
        print( "%s[distribution] cmd: %s%s" %(GREEN,cmd,RESET) )
    f=open("/tmp/create.log","a")
    f.write( "cmd: %s\n" %(cmd) )
    # print('CMD=',cmd)
    o=subprocess.check_output( cmd, shell=True )
    if len(o)>0:
        print("[distribution] %.80s" % o )
        f.write( str(o) + "\n" )
    f.close()
    return str(o)


def clearGlobalInfo( filename : str ):
    """ tidy up a given global info file """
    # print ( "[createTarballs] checking", filename )
    f=open(filename)
    lines=f.readlines()
    f.close()
    # fname = "/tmp/tmp.txt"
    fname = "/dev/shm/tmp.txt"
    g=open( fname,"wt")
    skip = [ "publishedData", "comment", "private", "checked", "xrange", \
             "prettyName", "susyProcess", "dataUrl", "validationTarball", "yrange" ]
    #skip.append( "validated" )
    # skip.append( "axes" )
    # skip.append( "figureUrl" )
    for line in lines:
        to_skip = False
        p1 = line.find("#")
        if p1 == 0:
            to_skip = True
        for s in skip:
            if line.find(s)==0:
                to_skip = True
        if not to_skip:
            g.write( line )
    g.close()
    cmd = f"cp {fname} {filename}"
    runCmd( cmd, prtMsg=False )

def clearJsons ( path : str ):
    """ clear the jsons in the given path. look at globalInfo.txt
        which jsons get used. ditch the rest. """
    gI = f"{path}/globalInfo.txt"
    if not os.path.exists ( gI ):
        return
    usedJsons = set()
    f = open ( gI, "rt" )
    lines = f.readlines()
    f.close()
    for i,line in enumerate(lines):
        p1 = line.find("#")
        if p1 >= 0:
            line = line[:p1]
        line = line.strip()
        if line == "":
            continue
        if not "jsonFiles:" in line and not "jsonFiles_FullLikelihood:" in line:
            continue
        txt = line.replace("jsonFiles:","")
        txt = txt.replace("jsonFiles_FullLikelihood:","")
        j=i
        while "{" in txt and not "}" in txt and not j >= (len(lines)-1):
            # seems like we need the next line
            j+=1
            txt += lines[j]
        try:
            D = eval(txt)
        except Exception as e:
            D = {}
        for k in D.keys():
            usedJsons.add ( k )
    jsons = glob.glob ( f"{path}/*.json" )
    for js in jsons:
        fname = os.path.basename ( js )
        remove = fname not in usedJsons
        if remove:
            print ( f"[createTarballs] removing {fname}" )
            os.unlink ( js )


if __name__ == "__main__":
    # FIXME maybe i find a better usage for this
    ap = argparse.ArgumentParser( description="cleaner for individual files" )
    defFile = "database/smodels-database/13TeV/CMS/CMS-PAS-SUS-16-052-eff/globalInfo.txt"
    ap.add_argument('-c', '--clean', help=f'name of tarball filename [{defFile}]',
                    type = str, default=defFile )
    args = ap.parse_args()
    clearGlobalInfo ( args.clean )

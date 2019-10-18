#!/usr/bin/env python3

import pickle, os, sys, subprocess, time, fcntl
from walker import Model # RandomWalker
from smodels.tools.physicsUnits import GeV
sys.path.insert(0,"../" )
from smodels_utils.plotting import rulerPlotter, decayPlotter
import helpers

def setup():
    codedir = "/mnt/hephy/pheno/ww/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
    os.chdir ( rundir )
    return rundir

def obtain ( number, picklefile ):
    """ obtain hiscore number <number> """
    if not os.path.exists ( picklefile ):
        print ( "[plotHiscore] hiscore.pcl does not exist. Trying to produce now with ./hiscore.py" )
        from argparse import Namespace
        args = Namespace()
        import hiscore
        hiscore.main ( *args )

    with open( picklefile,"rb" ) as f:
        #fcntl.flock( f, fcntl.LOCK_EX )
        hiscores = pickle.load ( f )
        trimmed = pickle.load ( f )
        #fcntl.flock( f, fcntl.LOCK_UN )
    if number < len(trimmed) and trimmed[number] is not None:
        Z = trimmed[number].Z
        print ( "[plotHiscore] obtaining trimmed model #%d: Z=%.2f (%d particles)" % (number, Z, len ( trimmed[number].unFrozenParticles() ) ) )
        return trimmed[number]
    Z = hiscores[number].Z
    print ( "[plotHiscore] obtaining untrimmed #%d: Z=%.2f" % (number, Z ) )
    return hiscores[ number ]

def gitCommit ( dest, wanted ):
    """ if wanted, then git commit and git push to smodels.githuib.io """
    if not wanted:
        return False
    cmd = "cd %s ; git commit -am 'update'; git push " % dest
    print ( "[plotHiscore] git-commit %s" % cmd )
    out = subprocess.getoutput ( cmd )
    if out != "":
        print ( "[plotHiscore] %s" % out )
    return True

def discussPredictions ( model ):
    print ( "How the Z comes about. Best combo:" )
    combo = model.bestCombo
    for pred in combo:
        print ( "theory pred: %s:%s" % ( pred.expResult.globalInfo.id, ",".join ( map ( str, pred.txnames ) ) ) )
        # print ( "     `- ", pred.expResult.globalInfo.id, "ana", pred.analysis, "masses", pred.mass, "txnames", pred.txnames, "type", pred.dataType() )

def writeTex ( model ):
    """ write the comment about ss multipliers and contributions, in tex """
    ssm = {}
    for k,v in model.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        pname = helpers.toLatex ( k )
        token = "%s = %.2f" % ( pname, v )
        if v in ssm.keys():
            v+=1e-10
        ssm[v] = token

    whatifs = ""
    if hasattr ( model, "whatif" ):
        print ( "[plotHiscore] contributions-by-particle are defined" )
        #whatifs+="\\\\Contributions by particles: $"
        whatifs+="\\\\"
        whatifs+="Contributions by particles: $"
        totalcont = 0. ## to normalize contributions
        for k,v in model.whatif.items():
            totalcont += (model.Z - v)
        tok = {}
        for k,v in model.whatif.items():
            if v in tok.keys():
                v+=1e-6
            tok[v] = "%s = %d%s" % ( helpers.toLatex(k), round(100.*(model.Z - v)/totalcont ), "\%" )
        keys = list ( tok.keys() )
        keys.sort()
        for v in keys:
            whatifs+= tok[v] + ", "
        if len(keys)>0:
            whatifs = whatifs[:-2]
        #whatifs+= ", ".join ( tok )
        whatifs+="$"
    else:
        print ( "[plotHiscore] model has no ``whatif'' defined (did you use an untrimmed model?)" )

    import tex2png
    if len(ssm) == 0:
        ssm = { 0: "\\mathrm{none}" }
    sssm = ""
    keys = list ( ssm.keys() )
    keys.sort( reverse=True )
    for k in keys:
        sssm += ssm[k] + ", "
    if len(keys)>0:
        sssm = sssm[:-2]
    src = "Signal strength multipliers: $" + sssm + "$" + whatifs
    # print ( "[plotHiscore] texdoc source in src=>>>>%s<<<<" % src )
    try:
        p = tex2png.Latex ( src, 600 ).write()
        f = open ( "texdoc.png", "wb" )
        f.write ( p[0] )
        f.close()
    except Exception as e:
        print ( "[plotHiscore] Exception when latexing: %s" % e )

def writeIndexHtml ( model ):
    ssm = []
    for k,v in model.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        ssm.append ( "%s: %.2f" % (helpers.getParticleName(k),v) )
    f=open("index.html","w")
    f.write ( "<html>\n" )
    f.write ( "<body>\n" )
    f.write ( "<center>\n" )
    f.write ( "<h1>Current best model: Z=%.2f</h1>\n" % model.Z )
    f.write ( "</center>\n" )
    f.write ( "<table width=80%>\n<tr><td>\n" )
    dbver = "???"
    strategy = "aggressive"
    if hasattr ( model, "dbversion" ):
        dbver = model.dbversion
        dotlessv = dbver.replace(".","")
    f.write ( "<b><a href=./hiscore.slha>Model</a> produced with <a href=https://smodels.github.io/docs/Validation%s>database v%s</a>, <br>combination strategy <a href=./matrix_%s.png>%s</a> in step %d</b><br>\n" % ( dotlessv, dbver, strategy, strategy, model.step ) )
    if hasattr ( model, "rvalues" ):
        rvalues=model.rvalues
        rvalues.sort(key=lambda x: x[0],reverse=True )
        f.write ( "<br><b>%d predictions available. Highest r values are:</b><br><ul>\n" % len(rvalues) )
        for rv in rvalues[:5]:
            srv="N/A"
            if type(rv[1])==float:
                srv="%.2f" % rv[1]
            f.write ( "<li>%s:%s r=%.2f, r<sub>exp</sub>=%s<br>\n" % ( rv[2].analysisId(), ",".join ( map(str,rv[2].txnames) ), rv[0], srv ) )
        f.write("</ul>\n")
    else:
        print ( "[plotHiscore] model has no r values!" )

    if hasattr ( model, "contributions" ):
        print ( "[plotHiscore] contributions-per-analysis are defined" )
        f.write ( "<td><br><b>Contributions per analysis:</b><br>\n<ul>\n" )
        conts = []
        for k,v in model.contributions.items():
            conts.append ( ( v, k ) )
        conts.sort( reverse=True )
        for v,k in conts:
            f.write ( "<li> %s: %s%s\n" % ( k, int(round(100.*v)), "%" ) )
        # f.write ( "</table>\n" )
    else:
        print ( "[plotHiscore] contributions are not defined" )

    height = 32*int((len(ssm)+3)/4)
    if ssm == []:
        height = 32
    if hasattr ( model, "whatif" ):
        height += 32
    f.write ( "<td><img width=600px src=./texdoc.png>\n" ) #  % height )
    f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</table>" )
    f.write ( '<table style="width:80%">\n' )
    f.write ( "<td width=45%><img height=650px src=./ruler.png><td width=55%><img height=650px src=./decays.png>\n" )
    f.write ( "</table>\n" )
    # f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</body>\n" )
    f.write ( "</html>\n" )
    f.close()
    print ( "[plotHiscore] Wrote index.html" )

def copyFilesToGithub():
    files = [ "hiscore.slha", "index.html", "matrix_aggressive.png", "decays.png", 
              "ruler.png", "texdoc.png" ]
    for f in files:
        if not os.path.exists ( f ):
            continue
        O = subprocess.getoutput ( "cp %s ../../smodels.github.io/models/" % f )
        if len(O)>0:
            print ( "[plotHiscore.py] when copying files: %s" % O )

def plotRuler( model ):
    resultsForPIDs = {}
    for tpred in model.bestCombo:
        for pid in tpred.PIDs:
            while type(pid) in [ list, tuple ]:
                pid = pid[0]
            apid = abs(pid)
            if not apid in resultsForPIDs:
                resultsForPIDs[apid]=set()
            resultsForPIDs[apid].add ( tpred.analysisId() )
    resultsFor = {}
    for pid,values in resultsForPIDs.items():
        resultsFor[ model.masses[pid] ] = values

    print ( "[plotHiscore] now draw ruler.png" )
    rulerPlotter.draw ( model.currentSLHA, "ruler.png", Range=(None,None),
                        mergesquark = False,
                        hasResultsFor = resultsFor )

def plotDecays ( model ):
    print ( "[plotHiscore] now draw decays.png" )
    options = { "tex": True, "color": True, "dot": True, "squarks": True,
                "weakinos": True, "sleptons": True, "neato": True,
                "integratesquarks": False, "leptons": True }
    options["rmin"] = 0.
    ## FIXME add cross sections.
    decayPlotter.draw ( model.currentSLHA, "decays.png", options,
                        ssmultipliers = model.ssmultipliers )

def plot ( number, verbosity, picklefile, options ):
    ## plot hiscore number "number"
    model = obtain ( number, picklefile )
    # print ( "[plotHiscore] create slha file" )
    fname = model.createSLHAFile ()
    subprocess.getoutput ( "cp %s hiscore.slha" % fname )
    opts = [ "ruler", "decays", "predictions", "copy", "html" ]
    for i in opts:
        if not i in options:
            options[i]=True

    plotruler = options["ruler"]
    if plotruler:
        plotRuler ( model )
    plotdecays = options["decays"]
    if plotdecays:
        plotDecays ( model )
    if options["predictions"]:
        discussPredictions ( model )
    if options["html"]:
        writeTex ( model )
        writeIndexHtml ( model )
    #if options["copy"]:
    #    copyFilesToGithub()

def main ():
    rundir = setup()
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore model plotter')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file to draw from [%shiscore.pcl]' % rundir,
            type=str, default="%shiscore.pcl" % rundir )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    argparser.add_argument ( '-H', '--nohtml',
            help='do not produce index.html',
            action="store_true" )
    argparser.add_argument ( '-R', '--noruler',
            help='do not produce ruler plot',
            action="store_true" )
    argparser.add_argument ( '-D', '--nodecays',
            help='do not produce decays plot',
            action="store_true" )
    argparser.add_argument ( '-p', '--predictions',
            help='list all predictions',
            action="store_true" )
    argparser.add_argument ( '-u', '--upload',
            help='upload to one of the following destinations: none, gpu, github, anomaly, interesting [none]. run --destinations to learn more', 
            type=str, default="" )
    argparser.add_argument ( '-c', '--commit',
            help='also commit and push to smodels.github.io (works only with -u github, anomaly, or interesting)',
            action="store_true" )
    argparser.add_argument ( "--destinations", 
            help="learn more about the upload destinations", action="store_true" )
    args = argparser.parse_args()
    if args.destinations:
        print ( "Upload destinations: " )
        print ( "      none: no upload" )
        print ( "       gpu: upload to GPU server, afs space." )
        print ( "            Result can be seen at http://www.hephy.at/user/wwaltenberger/models/" )
        print ( "    github: upload to github git directory." ) 
        print ( "            Result can be seen at https://smodels.github.io/models" )
        print ( "interesting: upload to github git directory, 'interesting' folder." )
        print ( "             Result can be seen at https://smodels.github.io/models/interesting" )
        print ( "anomaly: upload to github git directory, 'anomaly' folder." )
        print ( "             Result can be seen at https://smodels.github.io/models/anomaly" )
        return
    upload = args.upload.lower()
    if upload in [ "none", "" ]:
        upload = None

    options = { "ruler": not args.noruler, "decays": not args.nodecays,
                "predictions": args.predictions, "html": not args.nohtml }

    plot ( args.number, args.verbosity, args.picklefile, options )
    if upload is None:
        return
    F = "*.png hiscore.slha index.html"
    dest = ""
    if upload == "github":
        dest = "../../smodels.github.io/models/"
    if upload in [ "interesting", "anomaly" ]:
        dest = "../../smodels.github.io/models/%s/" % upload

    if dest != "":
        print ( "[plotHiscore] copying to %s" % dest )
        cmd = "cp %s %s" % ( F, dest )
        a = subprocess.getoutput ( cmd )
        if a != "":
            print ( "error: %s" % a )
            sys.exit()
        r = gitCommit( dest, args.commit )
        if not r:
            print ( "[plotHiscore] done. now please do yourself: " )
            print ( "cd %s" % dest )
            print ( "git commit -am 'update'" )
            print ( "git push" )
        return

    if upload == "gpu":
        import socket
        hostname = socket.gethostname()
        D = "/afs/hephy.at/user/w/wwaltenberger/www/models"
        ## first the backup
        if "gpu" in hostname:
            ## make backup
            cmd = "cp %s/* %s/backup/" % ( D, D )
        else:
            cmd = "ssh hepgpu01.hephy.oeaw.ac.at cp %s/* %s/backup/" % ( D, D )
        print ( cmd )
        # now the new stuff
        O = subprocess.getoutput ( cmd )
        if len(O)>0:
            print ( "[plotHiscore.py] when uploading files: %s" % O )

        if "gpu" in hostname:
            ## make backup
            cmd = "cp %s/* %s/backup/" % ( D, D )
            subprocess.getoutput ( cmd )
            cmd = "cp %s %s" % (F, D )
        else:
            cmd = "scp %s hepgpu01.hephy.oeaw.ac.at:%s" % ( F, D )
        print ( cmd )
        O = subprocess.getoutput ( cmd )
        if len(O)>0:
            print ( "[plotHiscore.py] when uploading files: %s" % O )
        return
    print ( "error, dont know what to do with upload sink '%s'" % upload )

if __name__ == "__main__":
    main()

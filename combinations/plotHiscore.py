#!/usr/bin/env python3

import pickle, os, sys, subprocess, time, fcntl
from walker import Model # RandomWalker
from smodels.tools.physicsUnits import GeV
sys.path.insert(0,"../" )
from smodels_utils.plotting import rulerPlotter, decayPlotter
import helpers

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
    if number in trimmed:
        Z = trimmed[number].Z
        print ( "[plotHiscore] obtaining trimmed #%d: Z=%.2f" % (number, Z ) )
        return trimmed[number]
    Z = hiscores[number].Z
    print ( "[plotHiscore] obtaining untrimmed #%d: Z=%.2f" % (number, Z ) )
    return hiscores[ number ]

def discussPredictions ( model ):
    print ( "How the Z comes about. Best combo:" )
    combo = model.bestCombo
    for pred in combo:
        print ( "theory pred: %s:%s" % ( pred.expResult.globalInfo.id, ",".join ( map ( str, pred.txnames ) ) ) )
        # print ( "     `- ", pred.expResult.globalInfo.id, "ana", pred.analysis, "masses", pred.mass, "txnames", pred.txnames, "type", pred.dataType() )

def writeTex ( model ):
    """ write the comment about ss multipliers and contributions, in tex """
    ssm = []
    for k,v in model.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        pname = helpers.toLatex ( k )
        ssm.append ( "%s = %.2f" % (pname,v) )

    whatifs = ""
    if hasattr ( model, "whatif" ):
        print ( "[plotHiscore] has whatifs defined" )
        #whatifs+="\\\\Contributions by particles: $"
        whatifs+="\\\\"
        whatifs+="Contributions by particles: $"
        totalcont = 0. ## to normalize contributions
        for k,v in model.whatif.items():
            totalcont += (model.Z - v) 
        tok = []
        for k,v in model.whatif.items():
            tok.append ( "%s = %d%s" % ( helpers.toLatex(k), round(100.*(model.Z - v)/totalcont ), "\%" ) )
        whatifs+= ", ".join ( tok )
        whatifs+="$"
    else:
        print ( "[plotHiscore] model has no ``whatif'' defined (did you use an untrimmed model?)" )

    import tex2png
    if ssm == []:
        ssm = [ "\\mathrm{none}" ]
    src = "Signal strength multipliers: $" + ", ".join ( ssm ) + "$" + whatifs
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
    if hasattr ( model, "dbversion" ):
        dbver = model.dbversion
        dotlessv = dbver.replace(".","")
    f.write ( "<b><a href=./hiscore.slha>Model</a> produced with <a href=https://smodels.github.io/docs/Validation%s>database v%s</a> in step %d</b><br>\n" % ( dotlessv, dbver, model.step ) )
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
        print ( "[plotHiscore] contributions are defined" )
        f.write ( "<td><br><b>Contributions per analysis:</b><br>\n<ul>\n" )
        for k,v in model.contributions.items():
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
    f.write ( "<td width=45%><img height=700px src=./ruler.png><td width=55%><img width=80% src=./decays.png>\n" )
    f.write ( "</table>\n" )
    # f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</body>\n" )
    f.write ( "</html>\n" )
    f.close()
    print ( "[plotHiscore] Wrote index.html" )

def copyFilesToGithub():
    subprocess.getoutput ( "cp hiscore.slha index.html matrix_aggressive.png decays.png ruler.png texdoc.png ../../smodels.github.io/models/" )

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
    ## FIXME add cross sections.
    decayPlotter.draw ( model.currentSLHA, "decays.png", options,
                        ssmultipliers = model.ssmultipliers )

def plot ( number, verbosity, picklefile, options ):
    ## plot hiscore number "number"
    model = obtain ( number, picklefile )
    print ( "[plotHiscore] create slha file" )
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
    if options["copy"]:
        copyFilesToGithub()

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore model plotter')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file to draw from [hiscore.pcl]',
            type=str, default="hiscore.pcl" )
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
            help='upload to GPU server, afs www space. To appear at http://www.hephy.at/user/wwaltenberger/models/',
            action="store_true" )
    args = argparser.parse_args()
    options = { "ruler": not args.noruler, "decays": not args.nodecays,
                "predictions": args.predictions, "html": not args.nohtml }
    plot ( args.number, args.verbosity, args.picklefile, options )
    if args.upload:
        import socket
        hostname = socket.gethostname()
        D = "/afs/hephy.at/user/w/wwaltenberger/www/models"
        F = "*.png hiscore.slha index.html"
        if "gpu" in hostname:
            cmd = "cp %s %s" % (F, D )
        else:
            cmd = "scp %s gpu:%s" % ( F, D )
        print ( cmd )
        subprocess.getoutput ( cmd )

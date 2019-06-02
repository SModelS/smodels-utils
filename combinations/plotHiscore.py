#!/usr/bin/env python3

import pickle, os, sys, subprocess, time
from randomWalk import Model # RandomWalker
from smodels.tools.physicsUnits import GeV
sys.path.insert(0,"../" )
from smodels_utils.plotting import rulerPlotter, decayPlotter
import helpers

def obtain ( number, picklefile ):
    """ obtain hiscore number <number> """
    f=open( picklefile,"rb" )
    hiscores = pickle.load ( f )
    f.close()
    Z = hiscores[number].Z
    print ( "[plotHiscore] obtaining #%d: Z=%.2f" % (number, Z ) )
    return hiscores[ number ]
    
def discussPredictions ( model ):
    print ( "How the Z comes about. Best combo:" )
    combo = model.bestCombo
    for pred in combo:
        print ( "theory pred: %s:%s" % ( pred.expResult.globalInfo.id, ",".join ( map ( str, pred.txnames ) ) ) )
        # print ( "     `- ", pred.expResult.globalInfo.id, "ana", pred.analysis, "masses", pred.mass, "txnames", pred.txnames, "type", pred.dataType() )

def toLatex ( pname ):
    """ get the latex version of particle name """
    rpls = { "L": "_{L}", "R": "_{R}", "1": "_{1}", "2": "_{2}", "~nu": "\\tilde{\\nu}",
             "~chi": "\\tilde{\\chi}", "~mu": "\\tilde{\\mu}", "+": "^{+}", "3": "_{3}", 
             "0": "^{0}", "-": "^{-}" }
    for kr,vr in rpls.items():
        pname = pname.replace(kr,vr)
    if pname.find("~")==0:
        p1,p2=1,2
        pname="\\tilde{"+pname[p1:p2]+"}"+pname[p2:]
    return pname

def writeTex ( model ):
    """ write the comment about ss multipliers and contributions, in tex """
    ssm = []
    for k,v in model.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        pname = toLatex ( helpers.getParticleName(k) )
        ssm.append ( "%s = %.2f" % (pname,v) )

    whatifs = ""
    if hasattr ( model, "whatif" ):
        whatifs+="\\\\Contributions by particles: $"
        #whatifs+="Contributions by particles: $"
        tok = []
        for k,v in model.whatif.items():
            tok.append ( "%s = %.2f" % ( toLatex(helpers.getParticleName(k)), model.Z - v ) )
        whatifs+= ", ".join ( tok )
        whatifs+="$"

    import tex2png
    src = "Signal strength multipliers: $" + ", ".join ( ssm ) + "$" + whatifs
    print ( "src=>>>>%s<<<<" % src )
    p = tex2png.Latex ( src, 600 ).write()
    f = open ( "texdoc.png", "wb" ) 
    f.write ( p[0] )
    f.close()

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
    f.write ( "Model produced in step %d<br>" % model.step )
    #f.write ( "<br>Signal strength multipliers: %s\n" % ", ".join ( ssm ) )
    height = 32*int((len(ssm)+3)/4)
    if hasattr ( model, "whatif" ):
        height += 32
    f.write ( "<br><img height=%dpt src=./texdoc.png>\n" % height )
    f.write ( '<p><table style="width:80%">\n' )
    f.write ( "<td width=35%><img src=./ruler.png><td width=65%><img width=100% src=./decays.png>\n" )
    f.write ( "</table>\n" )
    f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</body>\n" )
    f.write ( "</html>\n" )
    f.close()
    print ( "Wrote index.html" )

def copyFilesToGithub():
    subprocess.getoutput ( "cp index.html matrix_aggressive.png decays.png ruler.png ssmultipliers.png ../../smodels.github.io/models/" )

def plotRuler( model ):
    resultsForPIDs = {}
    for tpred in model.bestCombo:
        for pid in tpred.PIDs:
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
    model.createSLHAFile ()
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
            help='pickle file to draw from [best.pcl]',
            type=str, default="best.pcl" )
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
    argparser.add_argument ( '-s', '--scp',
            help='scp to smodels',
            action="store_true" )
    args = argparser.parse_args()
    options = { "ruler": not args.noruler, "decays": not args.nodecays, 
                "predictions": False, "html": not args.nohtml }
    plot ( args.number, args.verbosity, args.picklefile, options ) 
    if args.scp:
        print ( "scp to smodels" )
        subprocess.getoutput ( "scp *.png index.html smodels.hephy.at:/var/www/walten/models/" )

#!/usr/bin/env python3

import pickle, os, sys, subprocess, time
from randomWalk import Model # RandomWalker
from smodels.tools.physicsUnits import GeV
sys.path.insert(0,"../" )
from smodels_utils.plotting import rulerPlotter, decayPlotter

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

def writeIndexHtml ( model ):
    ssm = []
    for k,v in model.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        ssm.append ( "%s: %.2f" % (model.getParticleName(k),v) )
    f=open("index.html","w")
    f.write ( "<html>\n" )
    f.write ( "<body>\n" )
    f.write ( "<center>\n" )
    f.write ( "<h1>Current best model: Z=%.2f</h1>\n" % model.Z )
    f.write ( "</center>\n" )
    f.write ( "Model produced in step %d<br>" % model.step )
    f.write ( "<br>Signal strength multipliers: %s\n" % ", ".join ( ssm ) )
    f.write ( '<p><table style="width:80%">\n' )
    f.write ( "<td width=35%><img src=./ruler.png><td width=65%><img width=100% src=./decays.png>\n" )
    f.write ( "</table>\n" )
    f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</body>\n" )
    f.write ( "</html>\n" )
    f.close()
    print ( "Wrote index.html" )

def copyFilesToGithub():
    subprocess.getoutput ( "cp index.html matrix_aggressive.png decays.png ruler.png ../../smodels.github.io/models/" )

def plot ( number, verbosity, picklefile ):
    ## plot hiscore number "number"
    model = obtain ( number, picklefile )
    print ( "[plotHiscore] create slha file" )
    model.createSLHAFile ()
    
    def massToPid ( mass ):
        """ convert mass to pid """
        for pid,mm in model.masses.items():
            if abs(mass-mm)<.2:
                return pid
        return None

    plotRuler = True
    if plotRuler:
        resultsFor = {}
        for tpred in model.bestCombo:
            for branch in tpred.mass:
                mmass = branch[0].asNumber(GeV)
                mother = massToPid ( mmass )
                if not mmass in resultsFor:
                    resultsFor[mmass]=set()
                resultsFor[mmass].add ( tpred.expResult.globalInfo.id)
                # print ( "add", mmass, mother, tpred.expResult.globalInfo.id )
        print ( "[plotHiscore] now draw ruler.png" )
        rulerPlotter.draw ( model.currentSLHA, "ruler.png", Range=(None,None),
                            mergesquark = False,
                            hasResultsFor = resultsFor )
    plotDecays = True
    if plotDecays:
        print ( "[plotHiscore] now draw decays.png" )
        options = { "tex": True, "color": True, "dot": True, "squarks": True,
                    "weakinos": True, "sleptons": True, "neato": True,
                    "integratesquarks": False, "leptons": True }
        ## FIXME add cross sections.
        decayPlotter.draw ( model.currentSLHA, "decays.png", options, 
                            ssmultipliers = model.ssmultipliers )
    discussPredictions ( model )
    writeIndexHtml ( model )
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
    args = argparser.parse_args()
    plot ( args.number, args.verbosity, args.picklefile ) 

#!/usr/bin/env python3

from __future__ import print_function

"""
.. module:: decayPlotter
        :synopsis: With this module decay plots like 
        http://smodels.github.io/pics/example_decay.png
        can be created.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com> 

"""

import sys
sys.path.append('../../')
import logging
import logging.config
from smodels_utils import SModelSUtils
try:
    from . import setPath
except ImportError as e:
    pass
import os
from ptools import sparticleNames

def draw( slhafile : os.PathLike, outfile : os.PathLike, options : dict , 
          offset : float = 0., verbosity : str = "info" ):
    """ draw a decay plot from an slhafile
    :param options: dictionary with all optional parameters
    :param offset: FIXME what does that one do?
    """
    verbosity = verbosity.lower()
    levels = { "err": logging.ERROR, "warn": logging.WARN, "info": logging.INFO,
               "debug": logging.DEBUG }
    logLevel = 20
    for k,v in levels.items():
        if k in verbosity:
            logLevel = v
            logging.basicConfig ( level = logLevel )
    logger = logging.getLogger(__name__)

    out=os.path.basename ( slhafile ).replace(".slha","")
    if outfile!="":
        out=outfile
        if out.endswith(".png"):
            out = out.replace(".png","")

    if not "rmin" in options:
        options["rmin"]=0.

    for i in [ "leptons", "integratesquarks", "separatecharm", "verbose",
               "dot", "neato", "pdf", "nopng", "nopercentage", "simple", "squarks",\
               "sleptons", "weakinos", "zconstraints", "tex", "color",\
               "masses", "html" ]:
        if not i in options.keys(): options[i]=False
    if logLevel < 25:
        options["verbose"]=True

    verbosereader=False
    if options["verbose"]==True and not options["html"]: verbosereader=True
    from smodels_utils.plotting import decayPlots
    reader=decayPlots.SPhenoReader ( slhafile, verbose=verbosereader, \
            integrateLeptons=(not options["leptons"]),
            integrateSquarks=options["integratesquarks"],
            separatecharm=options["separatecharm"] )

    if options["verbose"]==True and not options["html"]:
        reader.printDecay("~g")
        logger.debug ( f"{reader.getDecays('~g', 0.9)}" )

    # tmp=[    "~g", "~q", "~b", "~t", "~t_1", "~t_2", "~b_1", "~b_2" ]
    tmp = { 1000021, 1000001, 1000005, 1000006, 2000005, 2000006 }

    if options["squarks"]:
        for pre in [ 1, 2 ]:
            for post in [ 1, 2, 3, 4 ]:
                tmp.add ( pre*1000000 + post )

    if options["sleptons"]:
        for pre in [ 1, 2 ]:
            for post in [ 11, 12, 13, 14, 15, 16 ]:
                tmp.add ( pre*1000000 + post )

    if options["weakinos"]:
        weakinos = { 1000022, 1000023, 1000024, 1000025, 1000035, 1000037 }
        tmp.update ( weakinos )

    starters=[]

    for i in tmp:
        if reader.hasTeVScaleMass(i):
            starters.append ( i )

    print ( f"[decayPlotters] we start with {starters}" )
    namer = sparticleNames.SParticleNames ( susy=False )

    ps=reader.getRelevantParticles ( reader.filterNames(starters), 
                                     rmin = options["rmin"] )

    extra={}
    if options["zconstraints"]:
        for i in [ 23, 24 ]:
            ds=reader.getDecays ( i, full=True, rmin = options["rmin"] )
            l=""
            first=True
            for d in ds:
                ## print ds[d].keys()
                l+="%s%s" % ( d, str ( ds[d].keys() ).replace("['","").replace("']","")    )
                if not first:
                    l+=", "
                first=False
            if len(l)>0:
                extra[reader.name ( i ) ] = l
    htmlbegin="<font size=-2 color='green'>"
    htmlend="</font>"
    if options["verbose"]:
        if options["html"]: print ( "<br>", htmlbegin )
        logger.debug ( f"We start from {starters}" )
        if options["html"]: print ( htmlend,"<br>" )
    drawer=decayPlots.DecayDrawer ( options, ps, offset, extra, verbosity )

    if options["tex"]:
        drawer.tex=True

    # now construct the nodes and the edges
    for pid in ps:
        color="#000000"
        if options["color"]:
            color=namer.rgbColor ( pid )
            # print ( "[decayPlotter] color of", pid,"is", color )
        m = reader.getMass ( pid )
        if m > 9e5: ## skip frozen particles
            continue
        drawer.addNode ( m, pid, \
                options["masses"], color, reader.fermionic ( pid ) )
        decs=reader.getDecays ( pid, rmin=options["rmin"] )
        drawer.addEdges ( pid, decs, rmin=options["rmin"] )

    ## drawer.addMassScale ( )

    if options["verbose"] and options["html"]:
        sout=out
        print ( htmlbegin,"[decayPlotter] now we draw!",sout,htmlend,"<br>" )
    drawer.draw ( out )

    if options["dot"] and options["tex"]:
        logger.debug ( "calling dot2tex." )
        drawer.dot2tex ( out )

if __name__ == "__main__":
    """ the script calls the drawing routine """
    import argparse

    argparser = argparse.ArgumentParser(description='SLHA to dot converter.')
    argparser.add_argument ( '-v', '--verbosity', 
            help='verbosity level -- debug, info, warning, error [info]',
            type=str, default="info" )
    argparser.add_argument ( '-sq', '--squarks',
            help='add squarks to list',action='store_true' )
    argparser.add_argument ( '-sl', '--sleptons',
            help='add sleptons to list',action='store_true' )
    argparser.add_argument ( '-w', '--weakinos',
            help='add weakinos to list',action='store_true' )
    argparser.add_argument ( '-m', '--masses',
            help='add mass labels',action='store_true' )
    argparser.add_argument ( '-Z', '--zconstraints',
            help='write down Z/W decay constraints',action='store_true' )
    argparser.add_argument ( '-l', '--leptons', help='have separate lepton flavors',\
            action='store_true' )
    argparser.add_argument ( '-i', '--integratesquarks',
            help='sum over different light squark flavors', action='store_true' )
    argparser.add_argument ( '-C', '--separatecharm',
            help='treat charm separately', action='store_true' )
    argparser.add_argument ( '-n', '--neato',
            help='create neato png file',action='store_true' )
    argparser.add_argument ( '-s', '--simple',
            help='simple names -- G instead of ~g, etc',action='store_true' )
    argparser.add_argument ( '--nopercentage',
            help='no percentages at all in labels',action='store_true' )
    argparser.add_argument ( '-N', '--nopng',
            help='dont create dot png file',action='store_true' )
    argparser.add_argument ( '-p', '--pdf',
            help='create dot pdf file',action='store_true' )
    argparser.add_argument ( '-d', '--dot', help='create dot file',
            action='store_true' )
    argparser.add_argument ( '-t', '--tex', help='tex characters',
            action='store_true' )
    argparser.add_argument ( '-c', '--color', help='use color',action='store_true' )
    argparser.add_argument ( '-O', '--offset', help='an offset in x in the plot',
                             type=int, default=0 )
    argparser.add_argument ( '-r', '--rmin', help='minimum br to still plot [0.]',
                             type=float, default=0. )
    argparser.add_argument ( '-f', '--filename', nargs='?', \
            help='slha input filename (spheno.slha)',
            type=str, default="spheno.slha" )

    argparser.add_argument ( '-o', '--outfile', nargs='?', \
            help='output filename (if not specified we use the slha filename '\
                 'with a different extension)', type=str, default="" )
    args=argparser.parse_args()
    Dict=args.__dict__
    options={}
    for (key,value) in Dict.items():
        if type(value)==bool:
            options[key]=value

    options["rmin"] = args.rmin

    draw( args.filename, args.outfile, options, args.offset,
          args.verbosity )

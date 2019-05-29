#!/usr/bin/env python3

from __future__ import print_function

"""
.. module:: decayPlotter
        :synopsis: With this module decay plots like 
        http://smodels.github.io/pics/example_decay.png
        can be created.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com> 

"""

def draw( slhafile, outfile, options, offset=0.,
          verbosity="info", ssmultipliers = None ):
    """ draw a decay plot from an slhafile
    :param offset: FIXME what does that one do?
    :param ssmultipliers: signal strength multipliers
    """
    import logging
    import logging.config
    from smodels_utils import SModelSUtils
    logging.config.fileConfig (
            SModelSUtils.installDirectory()+"/etc/commandline.conf" )
    logger = logging.getLogger(__name__)
    verbosity = verbosity.lower()
    levels = { "err": logging.ERROR, "warn": logging.WARN, "info": logging.INFO,
               "debug": logging.DEBUG }
    logLevel = 0
    for k,v in levels.items():
        if k in verbosity:
            logLevel = v
            logger.setLevel ( logLevel )

    import setPath
    from smodels_utils.plotting import decayPlots
    import os
    out=os.path.basename ( slhafile ).replace(".slha","")
    if outfile!="":
        out=outfile
        if out.endswith(".png"):
            out = out.replace(".png","")

    for i in [ "leptons", "integratesquarks", "separatecharm", "verbose",
               "dot", "neato", "pdf", "nopng", "nopercentage", "simple", "squarks",\
               "sleptons", "weakinos", "zconstraints", "tex", "color",\
               "masses", "html" ]:
        if not i in options.keys(): options[i]=False
    if logLevel > 15:
        options["verbose"]=True

    verbosereader=False
    if options["verbose"]==True and not options["html"]: verbosereader=True
    reader=decayPlots.SPhenoReader ( slhafile, verbose=verbosereader, \
            integrateLeptons=(not options["leptons"]),
            integrateSquarks=options["integratesquarks"],
            separatecharm=options["separatecharm"] )

    if options["verbose"]==True and not options["html"]:
        reader.printDecay("~g")
        logger.debug ( "%s" % reader.getDecays("~g",0.9) )

    tmp=[    "~g", "~q", "~b", "~t", "~t_1", "~t_2", "~b_1", "~b_2" ]
    if options["squarks"]:
        for i in [ "u", "d", "c", "s", "b", "t", "q" ]:
            for c in ["L", "R", "1", "2" ]:
                tmp.append ("~%s_%s" % ( i, c) )
                tmp.append ("~%s%s" % ( i, c) )

    if options["sleptons"]:
        for i in [ "l", "e", "mu", "tau", "nu", "nu_e", "nu_mu", "nu_tau" ]:
            for c in ["L", "R", "1", "2" ]:
                tmp.append ("~%s_%s" % ( i, c) )
                tmp.append ("~%s%s" % ( i, c) )

    if options["weakinos"]:
        map ( tmp.append, [ "~chi_1+", "~chi_2+", "~chi_20", "~chi_30" ] )

    starters=[]

    for i in tmp:
        if type ( reader.getMass(i) ) == type ( 5.0 ) or \
           type ( reader.getMass(i) ) == type ( 5 ):
            if reader.getMass(i)<100000:
                starters.append ( i )
        else:
            # add all else
            # print i,reader.getMass(i)
            starters.append ( i )

    colorizer=decayPlots.ByNameColorizer ( )

    ps=reader.getRelevantParticles ( reader.filterNames(starters) )
    # print ( "ps", ps )

    extra={}
    if options["zconstraints"]:
        for i in [ 23, 24 ]:
            ds=reader.getDecays ( i, full=True )
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
        logger.debug ( "We start from %s" % starters )
        if options["html"]: print ( htmlend,"<br>" )
    drawer=decayPlots.DecayDrawer ( options, ps, offset, extra, verbosity )

    if options["tex"]:
        drawer.tex=True

    # now construct the nodes and the edges
    for name in ps:
        color="#000000"
        if options["color"]:
            color=colorizer.getColor ( name )
        drawer.addNode ( reader.getMass ( name ), name, \
                options["masses"], color, reader.fermionic ( name ) )
        decs=reader.getDecays ( name, rmin=0.9 )
        drawer.addEdges ( name, decs )

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

    draw( args.filename, args.outfile, options, args.offset,
          args.verbosity )

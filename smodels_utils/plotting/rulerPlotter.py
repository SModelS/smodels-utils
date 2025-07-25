#!/usr/bin/env python3

"""
.. module:: rulerPlot
    :synopsis: Draws a ruler plot from e.g. an SLHA file, like
               http://smodels.github.io/pics/example_ruler.png

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

import os, math, sys, tempfile, numpy, subprocess
import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot as plt
import logging
import pyslha
sys.path.insert(0,"../../../protomodels/" )
from ptools.sparticleNames import SParticleNames

mpl.rcParams['figure.dpi'] = 300

def setLogLevel ( logger, verbose ):
    if "err" in verbose:
        logger.setLevel(logging.ERROR)
        return
    if "warn" in verbose:
        logger.setLevel(logging.WARN)
        return
    if "deb" in verbose:
        logger.setLevel(logging.DEBUG)
        return
    logger.setLevel(logging.INFO)

class RulerPlot:
    """ a class that encapsulates a horizontal ruler plot """
    def __init__ ( self, inputfile="masses.txt", outputfile="ruler", 
           Range=(None,None), formats={ "png": True }, printmass=False, 
           mergesquark=True, drawdecays=True, hasResultsFor = None, 
           verbosity="info", susy=False, trim= True, style="" ):
        """
        :param mergesquark: if True, merge squarks FIXME
        :param susy: use SUSY particle names
        :param style: emulate various styles, currently only "andre" is known
        """
        self.style = style
        self.inputfile = inputfile
        self.slhafile = inputfile
        for e in [ "png", "pdf", "eps" ]:
            if outputfile.endswith(f".{e}"):
                formats[e]=True
                outputfile = outputfile.replace(f".{e}","")
        self.outputfile = outputfile
        self.range = Range
        if sum ( formats.values() ) == 0:
            formats["png"]=True ## if nothing, then pngs
        self.formats = formats
        self.printmass = printmass
        self.mergesquark = mergesquark
        self.hasResultsFor = hasResultsFor 
        self.verbosity = verbosity
        self.logger=logging.getLogger("RulerPlot")
        self.susy = susy
        self.namer = SParticleNames ( susy = susy )
        self.decays = {}
        self.getMasses()
        self.getRange()
        self.drawdecays = drawdecays
        self.trim = trim
        if drawdecays:
            self.getDecays()

    def getMasses ( self ):
        """ obtain the masses from input file, remove > 3000 GeV """
        if self.inputfile.endswith ( ".slha" ):
            pmasses = self.retrieveMasses ()
        masses={}
        # masses=pmasses
        for (pid,D) in pmasses.items():
            masses[D["name"]] = D["m"]
        ## cut off at 3 TeV
        ret = [ m for m in masses.values() if m<3000. ]
        self.masses = ret
        self.logger.info ( f"masses {self.masses}" )
        return ret


    def getDecays ( self ):
        """ obtain the decays from input file, remove > 3000 GeV """
        f = pyslha.read ( self.slhafile )
        massblock = f.blocks["MASS"]
        mpids = []
        for mpid in massblock.keys():
            if massblock[mpid]<3000.:
                mpids.append ( mpid )
        decblock = f.decays
        decays = {}
        for mpid in mpids:
            dec = decblock[mpid].decays
            if len(dec)==0:
                continue
            for d in dec:
                if d.br < 1e-1: ## ignore too small branchings
                    continue
                if not mpid in decays:
                    decays[mpid]=[]
                decays[mpid].append( {"br": d.br, "ids": d.ids } )
        self.decays = decays

    def getRange ( self ):
        """ given self.masses, compute the range that we wish to plot. """
        maxvalue=max (self.masses)
        minvalue=min(self.masses)
        maxvalue = min ( [ 1.05*maxvalue, 3100. ] )
        minvalue = max ( [ 0, .95*minvalue ] )
        if minvalue > 480:
            minvalue = 480
        if maxvalue < 620:
            maxvalue = 620
        dm = maxvalue - minvalue
        if self.range[0] != None and self.range[0] >=0.:
            minvalue=self.range[0]
        if self.range[1] != None and self.range[1] >=0.:
            maxvalue=self.range[1]
        self.logger.info ( "range is [%d,%d]" % ( minvalue, maxvalue ) )
        self.minmass = minvalue
        self.maxmass = maxvalue

    def retrieveMasses ( self ):
        """ retrieve the masses from slha file """
        logger=logging.getLogger(__name__)
        logger.info ( f"now extracting masses from slha file {self.slhafile}" )
        namer = SParticleNames( susy = False )
        f = pyslha.read ( self.slhafile )
        m = f.blocks["MASS"]
        keys = m.keys()
        D={}
        for key in keys:
            mass = m[key]
            if mass > 4000.:
                continue
            name = namer.texName ( key )
            if namer.isSM ( key ): ## skip SM particles
                continue
            if self.mergesquark: ## sum up all squarks
                if namer.particleType ( key ) == "q":
                    name=name.rootName ( 1000001 )
            D[key]={ "name": name, "m": mass }
        self.masspids = D
        return D

    def getSortedPids ( self ):
        """ get a container of pids, sorted by the masses """
        sortedpids = []
        for (pid,D) in self.masspids.items():
            m = D["m"]
            sortedpids.append((m,pid))
        sortedpids.sort()
        pids = [ x[1] for x in sortedpids ]
        return pids

    def drawHorizontal ( self ):
        # https://pythonprogramming.net/spines-hline-matplotlib-tutorial/
        """ the matplotlib plotting function """
        plt.rc("text",usetex=True)
        dm = self.maxmass - self.minmass
        ticks = numpy.arange ( self.minmass, self.maxmass, .05*dm )
        y = [ 0. ] * len(ticks)
        y[0]=1.
        fig = plt.figure(figsize=(10,4))
        ax1 = plt.subplot()
        # ax1 = plt.subplot2grid((1,1), (0,0))
        labels = []
        for i,label in enumerate(ax1.xaxis.get_ticklabels()):
                    label.set_rotation(45)
                    labels.append ( label.get_label() ) #  " GeV" )
        ax1.spines['right'].set_color('none')
        ax1.spines['left'].set_color('none')
        ax1.spines['top'].set_color('none')
        ax1.plot ( ticks, y, c="w" )
        ax1.tick_params(axis='x', labelsize= 20, pad = 0 )
        ax1.set_yticks([])
        # plt.xlabel ( "m [GeV]" )
        plt.text(self.maxmass-10.,-.17,"m [GeV]", fontsize=25 )

        sortedpids = self.getSortedPids()

        for ctr,pid in enumerate(sortedpids):
            name = self.masspids[pid]["name"]
            m = self.masspids[pid]["m"]
            y=(abs(m)-self.minmass)/(self.maxmass-self.minmass)
            col=self.namer.rgbColor ( name )
            coldark=self.namer.rgbColor ( name, bold=True )
            label = f"${name}$" 
            yoff = 0. ## yoffset, put every second one halfway down
            if ctr % 2 == 1:
                yoff=.5
            plt.text ( m, .8-yoff, label, c = coldark, size=30, fontweight="bold" )
            lctr=0
            keys = []

            if self.hasResultsFor != None:
                for mana,analyses in self.hasResultsFor.items():
                    # print ( "m,mana",m,mana )
                    if abs(m-mana)<.1: ## max mass gap
                        if abs(m-mana)>1e-2:
                            print ( f"WARNING: clustering particle masses {m:.2f} and {mana:.2f}. hope its ok. check it."  )
                        keys.append ( mana )
                        for cana,ana in enumerate(analyses):
                            plt.text ( m-50., .91-yoff-.07*cana, ana.replace("201","1" ), c=col )
                            lctr+=1
        for frmat,runthis in self.formats.items():
            if not runthis:
                continue
            of = self.outputfile + "." + frmat
            self.logger.info ( f"saving to {of}" )
            plt.savefig ( of )
            if frmat == "png" and self.trim:
                cmd = f"convert {of} -trim {of}"
                subprocess.getoutput ( cmd )
        self.ax1 = ax1
        self.plt = plt

    def drawVertical ( self ):
        # https://pythonprogramming.net/spines-hline-matplotlib-tutorial/
        """ the matplotlib plotting function """
        from matplotlib import pyplot as plt
        plt.rc("text",usetex=True)
        import numpy
        deltam = self.maxmass - self.minmass
        fontsize = 15
        if self.style == "andre":
            fontsize = 20
        ticks = numpy.arange ( self.minmass, self.maxmass, .05*deltam )
        x = [ 0. ] * len(ticks)
        x[0]=1.
        figratio = ( 4, 10 )
        if self.drawdecays:
            figratio = ( 7, 4 )
        fig = plt.figure(figsize=figratio )
        ax1 = plt.subplot()
        labels = []
        for i,label in enumerate(ax1.yaxis.get_ticklabels()):
                    # label.set_rotation(45)
                    labels.append ( label.get_label() ) #  " GeV" )
        ax1.spines['right'].set_color('none')
        ax1.spines['left'].set_color('none')
        ax1.spines['top'].set_color('none')
        ax1.spines['bottom'].set_color('none')
        ax1.plot ( x, ticks, c="w" )
        ax1.set_xticks([])
        ax1.tick_params(axis='y', labelsize= fontsize-2, pad = 0 )
        if self.style == "andre":
            plt.text(-.22, self.maxmass+20., "m [GeV]", fontsize=fontsize )
        else:
            plt.text(-.22, self.minmass-30., "m [GeV]", fontsize=fontsize )

        sortedpids = self.getSortedPids()

        for ctr,pid in enumerate(sortedpids):
            name = self.masspids[pid]["name"]
            m = self.masspids[pid]["m"]
            # print ( "m", ctr, m, name )
            y=(abs(m)-self.minmass)/(self.maxmass-self.minmass)
            col=self.namer.rgbColor ( name )
            coldark=self.namer.rgbColor ( name, bold=True )
            label = f"${name}$" 
            ## compute the xoffset, we start at the center the move left and right
            xoff = 0.5 + (-1)**(ctr) * .15 * math.ceil(ctr/2)
            side = -1 ## -1 is left 1 is right
            if ctr % 2 == 0:
                side = 4.
            dtext=0.
            if ctr == 0:
                dtext =.05
            if ctr == 2:
                xoff += .03
            if self.style == "andre":
                xoff = 0.35 + (-1)**(ctr) * .05 * math.ceil(ctr/2)
                if ctr>0 and ctr%2 == 1:
                    dtext = -.17
                if ctr>0 and ctr%2 == 0:
                    dtext = .2
                if ctr == 0:
                    dtext = -.01
            #print  ( "ctr", ctr, "mass", label, m, "xoff", xoff, "dtext", dtext )
            plt.text ( xoff + dtext, m, label, c = coldark, size=fontsize, 
                       fontweight="bold", ha="left" )
            x1 = xoff + side * .05
            x2 = x1 + numpy.sign(side)*.1
            if ctr == 0:
                x2 = 1.
            ## small horizontal lines next to the particle names
            if self.style != "andre":
            ## thats the line to the right
                plt.plot ( [ x1, x2 ], [m+10. , m+10. ], c= coldark )

            ## the LBP gets horizontal lines in both directions 
            if ctr == 0:
                x1 = xoff - .05
                x2 = .03
                ## thats the line to the left
                # print ( "line m=", m, "x=", x1, x2 )
                plt.plot ( [ x1, x2 ], [m+10. , m+10. ], c= coldark )
                if len(sortedpids)>2:
                    plt.plot ( [ xoff + dtext+.1, .7 ], [m+10. , m+10. ], c= coldark )

            ## 
            ## at the center of the decay line
            xavg = .5*x1 + .5*x2
            lctr=0
            dm = deltam / 40.
            if self.drawdecays:
                dm = dm * 2.25 ## why though?
            keys = []

            if self.hasResultsFor != None:
                for mana,analyses in self.hasResultsFor.items():
                    # print ( "m,mana",m,mana )
                    if abs(m-mana)<.1: ## max mass gap
                        if abs(m-mana)>1e-2:
                            print ( f"WARNING: clustering particle masses {m:.2f} and {mana:.2f}. hope its ok. check it."  )
                        keys.append ( mana )
                        dm1 = deltam / 30. ## gap to first ana id
                        if self.drawdecays:
                            dm1 = dm1 * 1.83 ## why though?
                        for cana,ana in enumerate(analyses):
                            # print ( "[rulerPlotter] write %s at x=%.1f" % ( ana, xavg ) )
                            if xavg > .9:
                                xavg = .73
                            plt.text ( xavg, m-dm1-dm*cana, ana.replace("201","1" ),
                                       fontsize=fontsize, c=col, ha="center" )
                            lctr+=1

            if pid in self.decays:
                ## now check for decays
                decays = self.decays[pid]
                # print ( "[rulerPlotter] check for decays", decays )
                for d in decays[:1]:
                    ids = d["ids"]
                    br = d["br"]
                    idBSM = 1000022
                    idNotBSM = []
                    for iD in ids:
                        if abs(iD)>1000000:
                            idBSM = iD
                        else:
                            idNotBSM.append( abs(iD) )

                    mlow = self.masspids[idBSM]["m"] + 20.
                    # delta m that is due to ana ids
                    dmResults = lctr * dm + bool(lctr)*30.
                    mtop = m - dmResults - 10.
                    dm = mlow - m + 20. + dmResults
                    plt.arrow ( xavg, mtop, 0., dm , color="grey",
                               linewidth=2, 
                               head_length=15, head_width=.03 )
                    label = self.namer.texName(idNotBSM,addDollars=True) 
                    if br < 0.95:
                        label += f": {br}"
                    plt.text ( xavg + .05, mlow + 30., label, color="grey", 
                               size=fontsize-1 )
        for frmat,runthis in self.formats.items():
            if not runthis:
                continue
            of = self.outputfile + "." + frmat
            self.logger.info ( f"saving to {of}" )
            plt.savefig ( of )
            if frmat == "png" and self.trim:
                cmd = f"convert {of} -trim {of}"
                subprocess.getoutput ( cmd )

        self.ax1 = ax1
        self.plt = plt

    def interactiveShell( self ):
        import IPython
        IPython.embed()

if __name__ == "__main__":
    import argparse, types
    import setPath
    from smodels_utils import SModelSUtils
    argparser = argparse.ArgumentParser(description='Draws a "ruler-plot", i.e. particles arranged by their masses. See http://smodels.github.io/pics/example_ruler.png.')
    argparser.add_argument('inputfile', type=str, nargs=1,
                    help='input masses text file name, for an example see "etc/example_masses.txt". "@@installdir@@" will be replaced with the installation directory of smodels-utils. SLHA files are accepted, also.')
    argparser.add_argument ( '-m', '--min',
          help='minimal mass, -1 for automatic mode', type=int, default=-1 )
    argparser.add_argument ( '-M', '--max',
          help='maximum mass, -1 for automatic mode', type=int, default=-1 )
    argparser.add_argument ( '-o', '--output',
          help='output file name [@@input@@.png]', type=str, default='@@input@@.png' )
    argparser.add_argument ( '-R', '--hasResultsFor',
          help='hasResultsFor dictionary, given as string [""]', type=str, default='' )
    argparser.add_argument ( '-v', '--verbosity',
          help='verbosity -- debug, info, warning, error [info]', 
          type=str, default='info' )
    argparser.add_argument ( '-p', '--pdf', help='produce pdf', action='store_true' )
    argparser.add_argument ( '-t', '--trim', help='trim png', action='store_true' )
    argparser.add_argument ( '-e', '--eps', help='produce (=keep) eps',
                             action='store_true' )
    argparser.add_argument ( '-H', '--horizontal', 
            help='horizontal plot, not vertical', action='store_true' )
    argparser.add_argument ( '-I', '--interactive', 
            help='start interactive shell after plotting', action='store_true' )
    argparser.add_argument ( '-P', '--png', help='produce png', action='store_true' )
    argparser.add_argument ( '-a', '--andre', 
                             help='Andre style', action='store_true' )
    argparser.add_argument ( '-D', '--decays', 
                             help='draw decays', action='store_true' )
    argparser.add_argument ( '-mass', '--masses', help='write masses',
                             action='store_true' )
    argparser.add_argument ( '-squark', '--squark',
                             help='represent all squarks as ~q', action='store_true' )
    args=argparser.parse_args()
    Range=[args.min,args.max]
    formats= { "pdf":args.pdf, "eps":args.eps, "png":args.png }

    repl = os.path.basename ( args.inputfile[0]).replace(".slha","")
    args.output = args.output.replace("@@input@@",repl)

    inputfile=args.inputfile[0].replace("@@installdir@@",
                                        SModelSUtils.installDirectory() )
    import logging.config
    logging.config.fileConfig (
            SModelSUtils.installDirectory()+"/etc/commandline.conf" )
    logger=logging.getLogger(__name__)
    setLogLevel ( logger, args.verbosity.lower() )
    hasResultsFor = None
    if args.hasResultsFor != "":
        hasResultsFor = eval ( args.hasResultsFor )
    style = ""
    if args.andre:
        style = "andre"
    plotter = RulerPlot ( inputfile, args.output, Range, formats, args.masses, \
                          args.squark, args.decays, hasResultsFor,
                          trim = args.trim, style=style )
    if args.horizontal:
        plotter.drawHorizontal()
    else:
        plotter.drawVertical()

    if args.interactive:
        plotter.interactiveShell()

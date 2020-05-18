#!/usr/bin/env python3

"""
.. module:: rulerPlot
    :synopsis: Draws a ruler plot from e.g. an SLHA file, like
               http://smodels.github.io/pics/example_ruler.png

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

import os, math, sys, tempfile
import logging

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

def _printCanvas ( c1, filename ):
    """ tried to redirect stdout """
    logger=logging.getLogger(__name__)
    logger.debug ( "printing canvas to %s" % filename )
    import ROOT
    ROOT.gErrorIgnoreLevel=2000
    c1.Print(filename )
    ROOT.gErrorIgnoreLevel=-1

def _execute ( command ):
    try:
        import commands
    except ImportError:
        import subprocess as commands
    logger=logging.getLogger(__name__)
    logger.debug ( "now running %s" % command )
    out=commands.getoutput ( command )
    if len(out)!=0:
        logger.error( out )
        return False
    return True

def _squarkname ( Type, postfix ):
    """ create the ROOT.TLatex squark name """
    ret="#tilde{%s}" % Type
    if len(postfix)>0:
        ret+="_{%s}" % postfix
    return ret

def _color ( name ):
    """ different colors for different particle types """
    from ROOT import kGreen,kOrange,kRed,kBlue,kBlack
    Dict={ "~chi":kGreen+3,"~tau":kOrange+2,"~mu":kOrange+2,"~nu":kOrange+2,
        "~g":kRed+2,"~q":kBlue+3,"~u":kBlue+3,"~d":kBlue+3,"~c":kBlue+3,
        "~s":kBlue+3,"~t":kBlue+2,"~b":kBlue+2,"~e":kOrange+2,"~l":kOrange+2 }
    for (mname,color) in Dict.items():
        if name.find(mname)==0: return color
    return kBlack

def _pprint ( name ):
    """ find ROOT.TLatex names for various common names used in
      the comments in slha files  """
    Dict={ "A0":"A", "A1":"A^{1}", "H+":"H^{#pm}", "Hp":"H^{#pm}",
        "H2":"H^{2}", "H":"H", "h":"h", "~e":"#tilde{e}",
        "~g":"#tilde{g}", "~mu":"#tilde{#mu}", "~mu_L":"#tilde{#mu}_{L}",
        "~mu_R":"#tilde{#mu}_{R}", "~e_L":"#tilde{e}_{L}","~e_R":"#tilde{e}_{R}",
        "~tau_L":"#tilde{#tau}_{L}","~tau_R":"#tilde{#tau}_{R}",
        "~chi20":"#tilde{#chi}^{0}_{2}", "~chi30":"#tilde{#chi}^{0}_{3}",
        "~chi40":"#tilde{#chi}^{0}_{4}", "~chi50":"#tilde{#chi}^{0}_{5}",
        "~chi10":"#tilde{#chi}^{0}_{1}", "~chi1+":"#tilde{#chi}^{+}_{1}",
        "~chi2+":"#tilde{#chi}^{+}_{2}", "~chi3+":"#tilde{#chi}^{+}_{3}",
        "~chi4+":"#tilde{#chi}^{+}_{4}"
    }

    if name in Dict.keys (): 
        return Dict[name]
    ## allow curly brackets in name
    rawname=name.replace("{","").replace("}","")
    if rawname in Dict.keys (): 
        return Dict[rawname]

    if name.find("~nu_e")==0: return "#tilde{#nu}_{e}"
    if name.find("~nu_mu")==0: return "#tilde{#nu}_{#mu}"
    if name.find("~nu_tau")==0: return "#tilde{#nu}_{#tau}"
    if name.find("~d")==0: return _squarkname("d",name[2:])
    if name.find("~u")==0: return _squarkname("u",name[2:])
    if name.find("~s")==0: return _squarkname("s",name[2:])
    if name.find("~c")==0: return _squarkname("c",name[2:])
    if name.find("~t")==0: return _squarkname("t",name[2:])
    if name.find("~b")==0: return _squarkname("b",name[2:])

    if name.find("~")>-1:
        w=name.replace("~","#tilde{")
        w=w.replace("chi40", "chi^{0}_{4}" )
        w=w.replace("chi30", "chi^{0}_{3}" )
        w=w.replace("chi20", "chi^{0}_{2}" )
        w=w.replace("chi10", "chi^{0}_{1}" )
        w=w.replace("chi1+", "chi^{+}_{1}" )
        w=w.replace("chi2+", "chi^{+}_{2}" )
        w=w.replace("L", "_{L}" )
        w=w.replace("R", "_{R}" )
        w=w.replace("1", "_{1}" )
        w=w.replace("2", "_{2}" )
        w=w.replace("chi", "#chi" )
        name=w+"}"
    return name

def createDictionaryFromSLHA ( inputfile ):
    import pyslha
    print ( "creating dictionary" )
    sys.exit()

class RulerPlot:
    """ a class that encapsulates a horizontal ruler plot """
    def __init__ ( self, inputfile="masses.txt", outputfile="out", Range=(None,None),
           formats={ "png": True }, printmass=False, mergesquark=True,
           interactive = False, hasResultsFor = None, verbosity="info" ):
        """
        :param mergesquark: if True, merge squarks FIXME
        """
        self.inputfile = inputfile
        self.outputfile = outputfile
        self.range = Range
        self.formats = formats
        self.printmass = printmass
        self.mergesquark = mergesquark
        self.hasResultsFor = hasResultsFor 
        self.verbosity = verbosity
        self.logger=logging.getLogger("RulerPlot")
        self.interactive = interactive

    def getMasses ( self ):
        """ obtain the masses from input file, remove > 3000 GeV """
        if self.inputfile.endswith ( ".slha" ):
            self.inputfile = convertSLHAFile ( self.inputfile, self.mergesquark )
        f=open( self.inputfile )
        pmasses=eval(f.readline())
        f.close()

        masses={}
        # masses=pmasses
        for (key,value) in pmasses.items():
            if key.find("width")==-1:
                masses[key]=abs(value)
        ## cut off at 3 TeV
        ret = [ m for m in masses.values() if m<3000. ]
        self.masses = ret
        self.logger.info ( "masses %s" % self.masses )
        return ret

    def getRange ( self ):
        """ given self.masses, compute the range that we wish to plot. """
        maxvalue=max (self.masses)*1.05
        minvalue=min(self.masses)
        if maxvalue>3100:
            maxvalue=3100.
        dm = maxvalue - minvalue
        minvalue=minvalue - 0.05 * dm
        if minvalue < 0.:
            minvalue = 0.
        if self.range[0] != None and self.range[0] >=0.:
            minvalue=self.range[0]
        if self.range[1] != None and self.range[1] >=0.:
            maxvalue=self.range[1]
        self.logger.info ( "range is [%d,%d]" % ( minvalue, maxvalue ) )
        self.minmass = minvalue
        self.maxmass = maxvalue

    def plot ( self ):
        # https://pythonprogramming.net/spines-hline-matplotlib-tutorial/
        """ the matplotlib plotting function """
        from matplotlib import pyplot as plt
        import numpy
        dm = self.maxmass - self.minmass
        ticks = numpy.arange ( self.minmass, self.maxmass, .05*dm )
        y = [ 0. ] * len(ticks)
        fig = plt.figure()
        ax1 = plt.subplot2grid((1,1), (0,0))
        labels = []
        for i,label in enumerate(ax1.xaxis.get_ticklabels()):
                    label.set_rotation(45)
                    labels.append ( label.get_label() ) #  " GeV" )
        ax1.spines['right'].set_color('none')
        ax1.spines['top'].set_color('none')
        ax1.plot ( ticks, y, c="w" )
        ax1.set_yticks([])
        plt.xlabel ( "m [GeV]" )
        plt.savefig ( "horizontal.png" )
        self.ax1 = ax1
        self.plt = plt

    def interactiveShell( self ):
        if self.interactive == False:
            return
        import IPython
        IPython.embed()


    def draw ( self ):
        self.getMasses()
        self.getRange()
        self.plot()
        self.interactiveShell()

def drawVertical ( inputfile="masses.txt", outputfile="out", Range=(None,None),
           formats={ "png": True }, printmass=False, mergesquark=True,
           hasResultsFor = None, verbosity="info" ):
    """ entry point: draw the masses
      :param inputfile: the inputfilename, must contain a simple dictionary. If
                        the filename ends with .slha, create the dictionary on the fly.
      :param output: the output filename, without the extension.
      :param Range:  the range of the ruler, (min,max), given in GeV. -1 and None are for automatic mode (the script decides by itself).
      :param formats: the formats, as a dictionary. Supported are: eps, pdf, png.
      :param printmass: draw also mass values (in GeV)?
      :param mergesquark: If true, draw them as ~q
      :param hasResultsFor: a dictionary of what results exist for what mother 
           masses, e.g. { 504.4: {'ATLAS-SUSY-2015-02', 'ATLAS-SUSY-2015-03'} }
    """
    # print ( "[rulerPlotter] starting with %s" % hasResultsFor )
    if outputfile.endswith ( ".png" ):
        outputfile = outputfile.replace(".png","")
        formats["png"]=True

    if inputfile.endswith ( ".slha" ):
        inputfile = convertSLHAFile ( inputfile, mergesquark )
    f=open( inputfile )
    pmasses=eval(f.readline())
    f.close()

    masses={}
    # masses=pmasses
    for (key,value) in pmasses.items():
        if key.find("width")==-1:
            masses[key]=abs(value)
    hmasses= [ m for m in masses.values() if m<3000. ]
    maxvalue=max (hmasses)*1.05
    minvalue=min(masses.values())
    if maxvalue>3100:
        maxvalue=3100.
    dm = maxvalue - minvalue
    minvalue=minvalue - 0.05 * dm
    if minvalue < 0.:
        minvalue = 0.
    logger=logging.getLogger(__name__)
    if Range[0] != None and Range[0] >=0.:
        minvalue=Range[0]
    if Range[1] != None and Range[1] >=0.:
        maxvalue=Range[1]
    logger.info ( "range is [%d,%d]" % ( minvalue, maxvalue ) )

    import ROOT
    ROOT.gROOT.SetBatch()
    ROOT.gROOT.SetStyle("Plain")

    c1=ROOT.TCanvas("c1","c1",600,1000)

    tm = ROOT.TLatex()
    tm.SetNDC()
    tm.DrawLatex(.0,.03,"#splitline{  m}{[GeV]}" )

    lines=[]

    t=ROOT.TLatex()
    t.SetTextSize(0.05)

    ##set positions of lines & captions
    if printmass:
        xline0=0.27 #start of line
        xline1=0.35 #end of line
        xtext=0.39  #start of caption
    else:
        xline0=0.34
        xline1=0.43
        xtext=0.48

    ylist=[]
    for (name,m) in masses.items():
        y=(abs(m)-minvalue)/(maxvalue-minvalue)
        ylist.append(y)

    ydic={}
    for y in ylist:
      n=0
      for y2 in ylist:
          if math.fabs(y2-y)<0.02: n+=1
      ydic[y]=n

    written=[]

    sortedmasses = []
    for (name,m) in masses.items():
        if name[:5]=="width":
            continue
        if m > 5000.:
            continue
        sortedmasses.append((m,name))
    sortedmasses.sort()

    for ctr,(m,name) in enumerate(sortedmasses):
        y=(abs(m)-minvalue)/(maxvalue-minvalue)
        col=_color (name )
        l=ROOT.TLine(xline0,y,xline1,y)
        l.SetLineWidth(3)
        l.SetLineColor(col)
        if ydic[y]<4:
            offset=0.07
            t.SetTextSize(0.05)
        elif ydic[y]==4:
            offset=0.05
            t.SetTextSize(0.04)
        else:
            offset=0.04
            t.SetTextSize(0.03)
        l.Draw()
        lines.append(l)
        x=xtext
        xm=0.6
        dx = 0.
        if ctr % 2 == 1: ## all odd ones on the left
            x = xtext - .25
        else:
            dx = .1
        """
        # this was meant as some kind of crash resolution
        # mechanism, i think
        for coord in written:
            # print ( "coord0", coord[0]-y )
            if False: # math.fabs(coord[0]-y)<0.02:
                x=coord[1]+offset
                xm=coord[2]+2*offset
        """
        t.SetTextColor(col)
        label = _pprint(name)
        label = "#font[32]{%s}" % label
        t.DrawLatex(x+dx,y-.01,label )
        lctr=0
        keys = []
        if hasResultsFor != None:
            for mana,analyses in hasResultsFor.items():
                # print ( "m,mana",m,mana )
                if abs(m-mana)<.1: ## max mass gap
                    if abs(m-mana)>1e-2:
                        print ( "WARNING: clustering particle masses %.2f and %.2f. hope its ok. check it." % ( m, mana )  )
                    keys.append ( mana )
                    for ana in analyses:
                        t2 = ROOT.TLatex()
                        ddx=0.
                        if ctr % 2 == 0: ## all odd ones on the left
                            ddx=.29
                            t2.SetTextAlign(31)
                        t2.SetTextColor(col)
                        t2.SetTextSize(.025)
                        y_ = y-.037-.016*lctr
                        x_ = x-.07+ddx
                        t2.DrawLatex(x_,y_,ana.replace("201","1") )
                        lctr+=1
        for k in keys:
            hasResultsFor.pop ( k ) ## dont print them several times
        if printmass: t.DrawLatex(xm,y-.01,str(int(round(m,0))))
        written.append((y,x,xm))

    t.SetTextColor(ROOT.kBlack)
    for i in range ( int ( math.ceil ( minvalue / 100. )) * 100, \
                   int ( math.floor ( maxvalue / 100. )) * 100 +1, 100 ):
        y=(float(i)-minvalue)/(maxvalue-minvalue)
        l=ROOT.TLine ( 0.12,y,0.15,y) ## the black lines
        l.SetLineWidth(1)
        l.SetLineStyle(2)
        l.Draw()
        t.DrawLatex ( 0.01,y-0.01, str(i) )
        lines.append(l)

    tmpf=tempfile.mkstemp()[1]

    _printCanvas ( c1, tmpf+".eps" )
    for i in [ "pdf", "png", "eps" ]:
        if not i in formats: formats[i]=False

    if formats["pdf"]:
        logger.info ( "producing %s.pdf" % outputfile )
        _execute ( "epspdf %s.eps %s.pdf" % ( tmpf, outputfile ) )
    if formats["png"]:
        formats["eps"]=True
        crop=""
        _printCanvas ( c1, outputfile+"_direct.png" )
        if True and not printmass:
            crop="-crop 430x1200+0+0"
        _execute ( "convert %s %s_direct.png %s.png" % ( crop, outputfile, outputfile ) )
        #else:
        #    _execute ( "convert %s %s.eps %s_conv.png" % ( crop, tmpf, outputfile ) )
    if formats["eps"]:
        logger.info ( "producing %s.eps" % outputfile )
        _execute ( "cp %s.eps %s.eps" % (tmpf, outputfile ) )

    os.unlink ( tmpf )

def convertSLHAFile ( inputfile, collapse_squarks ):
    """
    :param collapse_squarks: replace all light squarks with ~q
    """
    outfile = "/tmp/masses.txt"
    logger=logging.getLogger(__name__)
    logger.info ( "now converting slha file %s to %s" % (inputfile, outfile) )
    import pyslha
    from smodels_utils.helper.sparticleNames import SParticleNames
    namer = SParticleNames()
    f = pyslha.read ( inputfile )
    m = f.blocks["MASS"]
    keys = m.keys()
    D={}
    for key in keys:
        mass = m[key]
        name = namer.name ( key )
        n = name.replace( "_R", "_{R}" ).replace ( "_L", "_{L}" )
        n = n.replace ( "_1", "_{1}" ).replace ( "_2", "_{2}" )
        n = n.replace ( "h+", "H^{+}" )
        n = n.replace ( "a0", "A^{0}" )
        n = n.replace ( "h1", "H" )
        n = n.replace ( "h2", "h" )
        if n in [ "W", "b", "H", "Z" ]: ## skip SM particles
            continue
        if collapse_squarks: ## sum up all squarks
            if namer.particleType ( key ) == "q":
                n="~q"
        D[n]=mass
    g=open ( "/tmp/masses.txt", "w" )
    g.write ( str(D) )
    g.close()
    return outfile

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
          help='output file name [ruler.png]', type=str, default='ruler.png' )
    argparser.add_argument ( '-R', '--hasResultsFor',
          help='hasResultsFor dictionary, given as string [""]', type=str, default='' )
    argparser.add_argument ( '-v', '--verbosity',
          help='verbosity -- debug, info, warning, error [info]', type=str, default='info' )
    argparser.add_argument ( '-p', '--pdf', help='produce pdf', action='store_true' )
    argparser.add_argument ( '-e', '--eps', help='produce (=keep) eps',
                             action='store_true' )
    argparser.add_argument ( '-H', '--horizontal', help='horizontal plot, not vertical',
                             action='store_true' )
    argparser.add_argument ( '-I', '--interactive', help='start interactive shell after plotting',
                             action='store_true' )
    argparser.add_argument ( '-P', '--png', help='produce png', action='store_true' )
    argparser.add_argument ( '-mass', '--masses', help='write masses',
                             action='store_true' )
    argparser.add_argument ( '-squark', '--squark',
                             help='represent all squarks as ~q', action='store_true' )
    args=argparser.parse_args()
    if not args.pdf and not args.eps:
        args.png = True ## if nothing, then pngs
    if args.output.endswith(".png"):
        args.png = True
        args.output = args.output.replace(".png","")
    Range=[args.min,args.max]
    formats= { "pdf":args.pdf, "eps":args.eps, "png":args.png }

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
    if args.horizontal:
        plotter = RulerPlot ( inputfile, args.output, Range, formats, args.masses, \
                              args.squark, args.interactive, hasResultsFor )
        plotter.draw()
    else:
        draw ( inputfile, args.output, Range, formats, args.masses, args.squark, \
               hasResultsFor )

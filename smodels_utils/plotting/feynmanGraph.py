#!/usr/bin/env python3

"""
.. module:: feynmanGraph
        :synopsis: This unit contains code to draw feynman graphs, in two
                   different styles: xkcd, and straight.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function
import logging
import math, random, os
logger = logging.getLogger(__name__)
import sys, copy
import subprocess
import pyx
if not hasattr ( pyx.text, "defaulttextrunner" ):
    pyx.text.defaulttexrunner = pyx.text.LatexEngine()
    pyx.text.set(pyx.text.LatexRunner)

from pyfeyn.user import color
from smodels.tools import runtime
from smodels.experiment.defaultFinalStates import SMfinalStates as SMList
from smodels.experiment.defaultFinalStates import BSMfinalStates as BSMList
from smodels.experiment import defaultFinalStates
BSMList += [ defaultFinalStates.RHadronD, defaultFinalStates.RHadronU ]

from smodels.theory.model import Model

def cleanConstraint ( inp ):
    """ cleanup constraint string """
    c = inp
    c=c.replace("71.*","").replace("(","").replace(")","").replace("`","")
    if c != inp:
        print ( "[feynmanGraph] modified", inp, "->", c )
    return c

def printParticle_ ( label ):
    """ very simple method to rename a few particles for the asciidraw
            routine, do not call directly """
    label = str ( label )
    # if not jet and label=="jet": label=r"q"
    # if jet and label=="jet": label=r"jet"
    if label in [ "gamma", "photon" ]: return r"\gamma" # r"\Pgamma"
    if label in [ "hi", "higgs" ]: label="H"
    if label in [ "f" ]: return r"\Pfermion"
    if label in [ "b" ]: return r"b"
    label=label+"     "
    return label[:3]

def segment_ ( p1, p2, spin, Bend=None ):
    from pyfeyn.user import NamedLine
    l=NamedLine[spin](p1,p2)#
    if Bend: l.bend(Bend)
    return l

def zero_ ():
    """ a super simple convenience thing to mark the (0,0) coordinates """
    c=Vertex(0.,0., mark=CIRCLE, fill=[ RED ] ) ## , radius=.01)
    c1=Vertex(1.0,0., mark=CIRCLE, fill=[ BLUE ] ) ## , radius=.01)
    c1=Vertex(0.,1., mark=CIRCLE, fill=[ BLUE ] ) ## , radius=.01)

class Drawer:
    def __init__ ( self, element, verbose ):
        self.element = element
        self.verbose = verbose
        self.f=1.0 ## no idea what that scales.


    def connect_ ( self, p1, p2, label=None, spin="fermion", bend=True,\
                   nspec=None, displace=None, col=color.rgb.black ):
        """ draw a line from p1 to p2
        :param canvas: the pyx canvas to draw on
        :param p1: starting point
        :param p2: end point
        :param label: add a label?
        :param nspec: specify the number of segment_s,
                      None is draw the number randomly
        :param displace: displace at fixed distance?
        :param color: color of line

        :returns: array of all line segment_s
        """
        from smodels_utils import SModelSUtils
        from pyfeyn.user import NamedLine, Fermion
        canvas = self.canvas
        verbose = self.verbose
        straight = self.straight

        if spin=="scalar" and not spin in NamedLine and "higgs" in NamedLine:
            spin="higgs"
        if straight:
            fl=NamedLine[spin](p1,p2)
            if col != color.rgb.black:
                fl.setStyles([ col ] )
                if spin in [ "vector" ]:
                    fl.setAmplitude(.1)
            if displace==None: displace=.05
            if label:
                # print "before replacement",label
                replacements = { "nu": "\\nu", "+": "^{+}", "-":"^{-}", "ta": "\\tau",
                                 "mu": "\\mu", "*": "\\mathrm{any}" }
                for r,rr in replacements.items():
                    #label=label.replace ( r, "$%s%" % rr )
                    label=label.replace ( r, rr )
                if label == "jet":
                    pass
                else:
                    label="$%s$" % label
                fl.addLabel ( label, pos=0.9, displace=displace )
            return [ fl ]

        fl=Fermion(p1,p2)
        fl.setStyles( [ color.rgb.white ] )
        n=nspec
        if n==None:
            n=int ( math.floor( random.uniform(1.5,3.75) ) )
        points = [ p1 ]
        f=.0001
        for i in range (1,n):
            pt=fl.fracpoint( float(i) / float(n) )
            pt.setX ( pt.x() + random.gauss( 0, f) )
            pt.setY ( pt.y() + random.gauss( 0, f) )
            points.append ( pt )
        points.append ( p2 )
        b=.015
        a=random.gauss ( 0, 1 )
        if a<0.: b=-b
        segs=[]
        # if verbose: print ( "[feynmanGraph.py] " )
        for i in range(n):
            br=b * (-1)**i
            if not bend: br=None
            segs.append ( segment_(points[i],points[i+1],spin, Bend=br ) )
            if verbose:
                print ( "[feynmanGraph.py] draw line from (%f,%f) to (%f,%f)" % ( points[i].x(), points[i].y(), points[i+1].x(), points[i+1].y() ) )
        if displace==None: displace=-.08
        # if label: segs[-1].addLabel ( label, pos=0.7, displace=displace )
        if label:
            lbl=label.replace(" ","").replace("_","").replace("$","").replace("+","")
            lbl=lbl.replace("-","")
            if lbl == "l": lbl="smallL"
            else:
                lbl=lbl.upper()
            if lbl == "\\PBEAUTY": lbl="B"
            filename="%s/icons/%s.jpg" % ( SModelSUtils.installDirectory(), lbl )
            #print "using",filename
            #print "filename=",filename
            from pyx import bitmap
            if not os.path.exists ( filename ):
                print ( "[feynmanGraph.py] error:",filename,"not found." )
                filename="%s/icons/questionmark.jpg" % SModelSUtils.installDirectory()
            try:
                jpg = bitmap.jpegimage( filename )
            except Exception as e:
                logger.error ( "cant load %s: %s!" % (filename,e) )
                import sys
                sys.exit(0)

            jpg = bitmap.jpegimage( filename )
            y1=segs[-1].fracpoint(1.0).y()
            y2=segs[-1].fracpoint(0.0).y()
            fp=0.90
            if y2>y1: fp=1.545
            pt=segs[-1].fracpoint(fp)

            # fd.currentCanvas.insert(bitmap.bitmap(0, 0, jpg, compressmode=None))
            canvas.insert(bitmap.bitmap(pt.x()+displace, pt.y(), jpg, compressmode=None))
        return segs

    def drawProtons ( self ):
        """ draw the incoming proton lines """
        from pyfeyn.user import Fermion
        from pyx import unit
        straight = self.straight
        vtx1=self.vtx1
        in1=self.in1
        in2=self.in2
        f=self.f
        f=.72
        if straight:
            P1a = Fermion(in1, vtx1 ).addLabel("P$_1$")
            P1a.addParallelArrow( pos=.44,displace=.0003,
                    length=unit.length(1.75*f), size=.0001)
            P1a.addParallelArrow( pos=.44,displace=-.0003,
                    length=unit.length(1.75*f), size=.0001)
        else:
            P1a = self.connect_ ( vtx1, in1, label="P$_1$", displace=.42 )

            for i in P1a:
                a1=i.addParallelArrow( pos=.44,displace=.0003,
                        length=unit.length(1.60*f / float(len(P1a))), size=.0001)
                a2=i.addParallelArrow( pos=.44,displace=-.0003,
                        length=unit.length(1.60*f / float(len(P1a))), size=.0001)
        if straight:
            P2a = Fermion(in2, vtx1 ).addLabel("P$_2$",displace=.3)
            P2a.addParallelArrow( pos=.44,displace=.0003,
                    length=unit.length(1.75*f), size=.0001)
            P2a.addParallelArrow( pos=.44,displace=-.0003,
                    length=unit.length(1.75*f), size=.0001)
        else:
            P2a = self.connect_ ( vtx1, in2, label="P$_2$", displace=.3 )
            for i in P2a:
                a1=i.addParallelArrow( pos=.44,displace=.0003,
                        length=unit.length(1.60*f / float(len(P2a))), size=.0001)
                a2=i.addParallelArrow( pos=.44,displace=-.0003,
                        length=unit.length(1.60*f / float(len(P2a))), size=.0001)

    def draw ( self, filename="bla.pdf", straight=False, inparts=True,
                     italic=False ):
        """ plot a lessagraph, write into pdf/eps/png file called <filename>
            :param straight: draw straight lines, or xkcd style
            :param inparts: draw the incoming lines and the big production blob?
            :param italic: labels in italic
        """
        verbose = self.verbose
        element = self.element
        f = self.f
        self.straight = straight
        import logging
        px =  logging.getLogger("pyx")
        px.setLevel ( logging.ERROR )

        try:
            from pyfeyn.user import FeynDiagram, Point, Circle, HATCHED135, CIRCLE, \
                Vertex, Fermion, Scalar
        except ImportError as e:
            logger.error ( "cannot draw, pyfeyn not installed? %s" % e )
            return
        try:
            fd = FeynDiagram()
            # jpg = bitmap.jpegimage("/home/walten/propaganda/cms/traverse.jpeg")

            in1    = Point(-1*f, -.75*f)
            in2    = Point(-1*f, 1.75*f)
            vtx1 = Circle(0,.5*f, radius=0.3*f).setFillStyle(HATCHED135)
            self.vtx1 = vtx1
            self.in1 = in1
            self.in2 = in2
            c=fd.currentCanvas
            self.canvas=c
            from pyx import unit
            if inparts:
                self.drawProtons()

            # nbranches=len(element.B)

            branches = copy.deepcopy ( element.branches )
            branches.reverse() ## first branch is top, second branch is bottom
            for (ct,branch) in enumerate(branches):
                if str(branch) == "[*]":
                    ## inclusive branch! draw joker
                    v1=Vertex ( f,f*ct,mark=CIRCLE)
                    f1 = self.connect_ ( vtx1, v1, spin="fermion", bend=True, nspec=3,
                           label = "*" ) ## "\\mathrm{any branch}" )
                    ## inclusive branch! skip it.
                    continue
                # p1 = Point(0, ct)
                lastVertex=vtx1
                nvtx=0
                for ( nvtx,(insertions,oddptcl)) in enumerate(zip(branch.evenParticles,branch.oddParticles)):
                    mark=None
                    if len(insertions)>0:
                        mark=CIRCLE
                    # mark=None
                    v1=Vertex ( f*(nvtx+1),f*ct,mark=mark)
                    col = color.rgb.black
                    if oddptcl.label in [ "longlived" ]:
                        col = color.rgb.red
                        #from pyfeyn.user import BLUE
                        #col = BLUE
                    # f1 = Scalar    ( lastVertex,v1) ## .addLabel ( "x")
                    f1 = self.connect_ ( lastVertex,v1, spin="scalar",
                                         bend=True, nspec=3, col=col )
                    if straight:
                        if nvtx==0:
                            b=.10
                            if ct==1: b=-.1
                            for xf in f1: xf.bend(b)
                    lastVertex=v1
                    # print "particles",particles,"ct=",ct
                    y=-1.0*f ## y of end point of SM particle
                    if ct==1: y=2.*f
                    dx=(len(insertions)-1)*(-.25)*f ## delta_x
                    #dx=(particles-1)*(-.5)*f ## delta_x
                    for (i,insertion) in enumerate(insertions):
                        x_c=f*(nvtx + 1 +    dx + 0.5*i)
                        y_c=f*y
                        p=Point ( x_c, y_c )
                        # print "add point at",x_c,y_c
                        ## print "branch=",branch
                        label=printParticle_ ( insertion )
                        ## ff=Fermion(v1,p).addLabel ( label )
                        # if italic: label="$%s$" % label
                        # print "label=",label
                        self.connect_ ( v1, p, label=label, displace=.1 )

                pl = Point ( nvtx+2,ct )
                fState = "MET"
                if hasattr ( branch, "finalState" ):
                    fState = branch.finalState
                if hasattr ( element, "getFinalStates" ):
                    fState = str ( element.getFinalStates()[ct] )
                c = color.rgb.black
                s = "scalar"
                colors = { "MET": color.rgb.black, "HSCP": color.rgb.red, "RHadronG": color.rgb.red,
                           "RHadronQ": color.rgb.red }
                spins = { "MET": "scalar", "HSCP": "scalar", "RHadronG": "vector",
                           "RHadronQ": "fermion" }
                if fState in colors:
                    c = colors[fState]
                if fState in spins:
                    s = spins[fState]
                self.connect_ ( lastVertex,pl, spin=s, col=c )
            extensions = [ "png", "svg", "jpg", "jpeg" ]
            pdffile=filename
            for e in extensions: pdffile=pdffile.replace( e, "pdf" )
            # epsfile=pdffile.replace("pdf","eps")
            fd.draw( pdffile )
            #fd.draw( epsfile )
            if pdffile!=filename:
                cmd = "convert -quiet %s %s" % ( pdffile, filename )
                a = subprocess.getoutput ( cmd )
                if a != "":
                    logger.error ( "file format conversion failed: %s" % a )
                    sys.exit()
        except Exception as e:
            logger.error ( "[draw] exception %s" % e )

if __name__ == "__main__":
        import setPath, argparse, types

        argparser = argparse.ArgumentParser(description=
                'simple tool that is meant to draw lessagraphs, '
                'as a pdf feynman plot')
        argparser.add_argument ( '-T', nargs='?',
                help='Tx name, will look up lhe file in ../regression/Tx_1.lhe. '
                     'Will be overriden by the "--lhe" argument',
                     type=str, default='T1' )
        argparser.add_argument ( '-l', '--lhe', nargs='?',
                      help='lhe file name, supplied directly. '
                          'Takes precedence over "-T" argument.',
                      type=str, default='' )
        argparser.add_argument ( '-c', '--constraint', nargs='?',
                      help='create graph from SModelS constraint '
                          'Takes precedence over "-T" and "-l" arguments.',
                      type=str, default='' )
        argparser.add_argument ( '-f', '--final_state', nargs='?',
                      help='specify final state ("MET","MET"). Used only in combination with -c.',
                      type=str, default='("MET","MET")' )
        argparser.add_argument ( '-L', '--long_lived', nargs='?',
                      help='specify which BSM particle is long lived (if any), e.g [[0],[0]]. Used only in combination with -c.',
                      type=str, default='' )
        argparser.add_argument ( '-o', '--output', nargs='?',
                help= 'output file, can be pdf or eps or png (via convert)',
                type=str, default='out.pdf' )
        argparser.add_argument ( '-s', '--straight', help='straight, not xkcd style',
                                 action='store_true' )
        argparser.add_argument ( '-I', '--italic', action='store_true',
                help='write labels in italic (only in straight mode' )
        argparser.add_argument ( '-i', '--incoming', help='draw incoming particles',
                                 action='store_true' )
        argparser.add_argument ( '-v', '--verbose', help='be verbose',
                                 action='store_true' )
        args=argparser.parse_args()

        from smodels.theory import crossSection, element
        from smodels_utils import SModelSUtils
        import sys

        strt = args.straight
        outdir = os.path.dirname( args.output )
        outfile = os.path.basename ( args.output )

        if args.constraint!="":
            fs = args.final_state.replace("(","[").replace(")","]")
            fs = eval (fs )
            constraint = args.constraint.replace(" ","" )
            mergefiles, delfiles = "", ""
            if "]+[" in constraint:
                constraints = constraint.split("]+[")
                # print ( "[feynmanGraph] sum of elements" )
                for i,c in enumerate(constraints):
                    out = outdir + "/" + outfile.replace(".","%d." % i ).replace(".png",".pdf")
                    df = outdir + "/"+  outfile.replace(".","%d." % i )
                    mergefiles += out + " "
                    delfiles += out + " "
                    if i < (len(constraints)-1):
                        c+="]"
                        # mergefiles += "plus.pdf "
                    if i > 0:
                        c="["+c
                    cc = cleanConstraint ( c )
                    model = Model( BSMparticles=BSMList, SMparticles=SMList )
                    E = element.Element ( cc, model=model )
                    drawer = Drawer ( E, args.verbose )
                    drawer.draw ( out, straight=strt, inparts=args.incoming,
                                  italic=args.italic )
                    del drawer
                nx,ny = 1,1
                if len(constraints)>1:
                    nx = math.ceil ( len(constraints) / 2. )
                    if nx == 1: nx = 2
                if len(constraints)>2:
                    ny = 2
                pdfout = args.output.replace(".png",".pdf")
                C = "pdfjam %s --nup %dx%s --landscape --outfile %s" % ( mergefiles, nx, ny, pdfout )
                print ( "C=", C )
                o = subprocess.getoutput ( C )
                if len(o)>0:
                    print ( "o=", o )
                C = "rm %s" % delfiles
                o = subprocess.getoutput ( C )
                #if len(o)>0:
                #    print ( "o=", o )
                C = "pdfcrop %s tmp.pdf" % ( pdfout )
                o = subprocess.getoutput ( C )
                if len(o)>0:
                    print ( "o=", o )
                C = "mv tmp.pdf %s" % ( pdfout )
                o = subprocess.getoutput ( C )
                if len(o)>0:
                    print ( "o=", o )
                if ".png" in args.output:
                    C="convert %s %s" % ( pdfout ,args.output )
                    o = subprocess.getoutput ( C )
                    print ( "o=", o )
                sys.exit()
            constraint = cleanConstraint ( args.constraint )
            runtime.modelFile = 'smodels.share.models.mssm'
            model = Model( BSMparticles=BSMList, SMparticles=SMList )
            E=element.Element ( constraint, fs, model=model )
            if args.long_lived:
                if not args.long_lived.count("[")==3 or not args.long_lived.count("]")==3:
                    print ( "error: syntax for long lived: [[i,j],[k,l]]. Give the indices of the long lived particles for each branch." )
                    sys.exit()
                ll = eval ( args.long_lived )
                for ctrb,b in enumerate(E.branches):
                    for ctrp,op in enumerate(b.oddParticles):
                        if ctrp in ll[ctrb]:
                            b.oddParticles[0].label="longlived"

            drawer = Drawer ( E, args.verbose )
            drawer.draw ( args.output, straight=strt, inparts=args.incoming,
                          italic=args.italic )
            #del drawer ## no fucking clue why this is needed
            sys.exit()

        print ( "LHE mode currently not working." )
        """
        filename="%s/lhe/%s_1.lhe" % (SModelSUtils.installDirectory(), args.T )
        if args.lhe!="": filename=args.lhe

        from smodels.theory import lheReader
        import lheDecomposer
        reader = lheReader.LheReader( filename )
        Event = reader.next()
        E = lheDecomposer.elementFromEvent( Event, crossSection.XSectionList() )
        drawer = Drawer ( E, args.verbose )
        drawer.draw ( args.output, straight=args.straight, inparts=args.incoming,
                      italic=args.italic )
        del drawer ## no fucking clue why this is needed
        """

#!/usr/bin/env python3

"""
.. module:: rulerPlot
    :synopsis: Draws a ruler plot from e.g. an SLHA file, like
               http://smodels.github.io/pics/example_ruler.png

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

import os, math, sys, tempfile, ROOT
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
    Dict={ "~chi":kGreen+2,"~tau":kOrange+2,"~mu":kOrange+2,"~nu":kOrange+2,
        "~g":kRed,"~q":kBlue+2,"~u":kBlue+2,"~d":kBlue+2,"~c":kBlue+2,
        "~s":kBlue+2,"~t":kBlue+1,"~b":kBlue+1,"~e":kOrange+2,"~l":kOrange+2 }
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

def draw ( inputfile="masses.txt", outputfile="out", Range=(None,None),
           formats={ "png": True }, printmass=False, mergesquark=True,
           hasResultsFor = None ):
    """ entry point: draw the masses
      :param inputfile: the inputfilename, must contain a simple dictionary. If
                        the filename ends with .slha, create the ditionary on the fly.
      :param output: the output filename, without the extension.
      :param Range:  the range of the ruler, (min,max), given in GeV. -1 and None are for automatic mode (the script decides by itself).
      :param formats: the formats, as a dictionary. Supported are: eps, pdf, png.
      :param printmass: draw also mass values (in GeV)?
      :param mergesquark: If true, draw them as ~q
      :param hasResultsFor: a dictionary of what results exist for what mother 
           masses, e.g. { 504.4: {'ATLAS-SUSY-2015-02', 'ATLAS-SUSY-2015-03'} }
    """
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
    maxvalue=max (hmasses)*1.05 #  max(masses.values())*1.05
    if maxvalue>3100:
        maxvalue=3100.
    minvalue=min(masses.values())*0.80-60.
    if minvalue < 0.:
        minvalue = 0.
    logger=logging.getLogger(__name__)
    if Range[0] != None and Range[0] >=0.:
        minvalue=Range[0]
    if Range[1] != None and Range[1] >=0.:
        maxvalue=Range[1]
    logger.info ( "range is [%d,%d]" % ( minvalue, maxvalue ) )

    ROOT.gROOT.SetBatch()
    ROOT.gROOT.SetStyle("Plain")

    c1=ROOT.TCanvas("c1","c1",300,600)

    lines=[]

    t=ROOT.TLatex()
    t.SetTextSize(0.05)

    ##set positions of lines & captions
    if printmass:
        xline0=0.20 #start of line
        xline1=0.35 #end of line
        xtext=0.37  #start of caption
    else:
        xline0=0.23
        xline1=0.40
        xtext=0.42

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

    for (name,m) in masses.items():
        if name[:5]=="width":
            continue
        if m > 5000.:
            continue
        y=(abs(m)-minvalue)/(maxvalue-minvalue)
        col=_color (name )
        l=ROOT.TLine(xline0,y,xline1,y)
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
        for coord in written:
            if math.fabs(coord[0]-y)<0.02:
                x=coord[1]+offset
                xm=coord[2]+2*offset
        t.SetTextColor(col)
        label = _pprint(name)
        t.DrawLatex(x,y-.01,label )
        ctr=0
        keys = []
        for mana,analyses in hasResultsFor.items():
            # print ( "m,mana",m,mana )
            if abs(m-mana)<10.:
                if abs(m-mana)>.1:
                    print ( "WARNING: clustering particles. hope its ok. check it." )
                keys.append ( mana )
                for ana in analyses:
                    t2 = ROOT.TLatex()
                    t2.SetTextColor(col)
                    t2.SetTextSize(.03)
                    t2.DrawLatex(x-.07,y-.037-.018*ctr,ana )
                    ctr+=1
        for k in keys:
            hasResultsFor.pop ( k ) ## dont print them several times
        if printmass: t.DrawLatex(xm,y-.01,str(int(round(m,0))))
        written.append((y,x,xm))

    t.SetTextColor(ROOT.kBlack)
    for i in range ( int ( math.ceil ( minvalue / 100. )) * 100, \
                   int ( math.floor ( maxvalue / 100. )) * 100 +1, 100 ):
        y=(float(i)-minvalue)/(maxvalue-minvalue)
        l=ROOT.TLine ( 0.13,y,0.16,y)
        l.SetLineWidth(3)
        l.Draw()
        t.DrawLatex ( 0.02,y-0.01, str(i) )
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
        if True and not printmass:
            crop="-crop 270x1200+0+0"
        logger.info ( "producing %s.png" % outputfile )
        _execute ( "convert %s %s.eps %s.png" % ( crop, tmpf, outputfile ) )
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
    argparser.add_argument ( '-v', '--verbosity',
          help='verbosity -- debug, info, warning, error [info]', type=str, default='info' )
    argparser.add_argument ( '-p', '--pdf', help='produce pdf', action='store_true' )
    argparser.add_argument ( '-e', '--eps', help='produce (=keep) eps',
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
    draw ( inputfile, args.output, Range, formats, args.masses, args.squark )

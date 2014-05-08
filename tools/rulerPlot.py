#!/usr/bin/env python

""" 
.. module:: rulerPlot
    :synopsis: Draws a ruler plot, like http://smodels.hephy.at/images/example_ruler.png.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import ROOT, os, math, sys, tempfile

def _printCanvas ( c1, filename ):
  #print "start redirect"
  #Tmp=sys.stdout
  #f=open("/dev/null","w")
  #sys.stderr=f
  #sys.stdout=f
  #print "!dhufdhuf"
  c1.Print(filename )
  #sys.stdout=Tmp
  #sys.stderr=Tmp
  #f.close()
  #print "end redirect"

def _execute ( command ):
    import commands
    out=commands.getoutput ( command )
    if len(out)!=0:
      print "[rulerPlot.py] errror",out
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
    from ROOT import kGreen,kOrange,kRed,kBlue
    Dict={ "~chi":kGreen+2,"~tau":kOrange+2,"~mu":kOrange+2,"~nu":kOrange+2,
        "~g":kRed,"~q":kBlue+2,"~u":kBlue+2,"~d":kBlue+2,"~c":kBlue+2,
        "~s":kBlue+2,"~t":kBlue+1,"~b":kBlue+1,"~e":kOrange+2,"~l":kOrange+2 }
    for (mname,color) in Dict.items():
        if name.find(mname)==0: return color 
    return ROOT.kBlack

def _pprint ( name ):
  """ find ROOT.TLatex names for various common names used in
      the comments in slha files  """
  #Dict={ "A0":"a^{0}", "A1":"a^{1}", "H+":"h^{#pm}", "Hp":"h^{#pm}", 
  #  "H2":"h^{3}", "H":"h^{2}", "h":"h^{1}", "~e":"#tilde{e}", 
  #  "~g":"#tilde{g}", "~mu":"#tilde{#mu}", "~mu_L":"#tilde{#mu}_{L}",
  #  "~mu_R":"#tilde{#mu}_{R}", "~e_L":"#tilde{e}_{L}","~e_R":"#tilde{e}_{R}",
  #  "~tau_L":"#tilde{#tau}_{L}","~tau_R":"#tilde{#tau}_{R}",
  #  "~chi20":"#tilde{#chi}^{0}_{2}", "~chi30":"#tilde{#chi}^{0}_{3}",
  #  "~chi40":"#tilde{#chi}^{0}_{4}", "~chi50":"#tilde{#chi}^{0}_{5}",
  #  "~chi10":"#tilde{#chi}^{0}_{1}", "~chi1+":"#tilde{#chi}^{+}_{1}",
  #  "~chi2+":"#tilde{#chi}^{+}_{2}", "~chi3+":"#tilde{#chi}^{+}_{3}",
  #  "~chi4+":"#tilde{#chi}^{+}_{4}" }
  Dict={ "A0":"A", "A1":"A^{1}", "H+":"H^{#pm}", "Hp":"H^{#pm}", 
    "H2":"H^{2}", "H":"H", "h":"h", "~e":"#tilde{e}", 
    "~g":"#tilde{g}", "~mu":"#tilde{#mu}", "~mu_L":"#tilde{#mu}_{L}",
    "~mu_R":"#tilde{#mu}_{R}", "~e_L":"#tilde{e}_{L}","~e_R":"#tilde{e}_{R}",
    "~tau_L":"#tilde{#tau}_{L}","~tau_R":"#tilde{#tau}_{R}",
    "~chi20":"#tilde{#chi}^{0}_{2}", "~chi30":"#tilde{#chi}^{0}_{3}",
    "~chi40":"#tilde{#chi}^{0}_{4}", "~chi50":"#tilde{#chi}^{0}_{5}",
    "~chi10":"#tilde{#chi}^{0}_{1}", "~chi1+":"#tilde{#chi}^{+}_{1}",
    "~chi2+":"#tilde{#chi}^{+}_{2}", "~chi3+":"#tilde{#chi}^{+}_{3}",
    "~chi4+":"#tilde{#chi}^{+}_{4}" }
  if Dict.has_key ( name ): return Dict[name]

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

def draw ( inputfile="masses.txt", outputfile="out", Range=[-1,-1], 
           formats={ "png": True }, printmass=False ):
  """ entry point: draw the masses 
      :param inputfile: the inputfilename, must contain a simple dictionary. 
      :param output: the output filename, without the extension.
      :param Range:  the range of the ruler, [min,max], given in GeV. -1 is for automatic mode (the script decides by itself).
      :param formats: the formats, as a dictionary. Supported are: eps, pdf, png.
      :param printmass: draw also mass values (in GeV)?
  """

  f=open( inputfile )
  pmasses=eval(f.readline())
  f.close()

  masses={}
  # masses=pmasses
  for (key,value) in pmasses.items():
    if key.find("width")==-1:
      masses[key]=abs(value)
  maxvalue=max(masses.values())*1.05
  if maxvalue>3100: maxvalue=3100.
  minvalue=min(masses.values())*0.80
  #print "[ruler.py] user wanted",Range[0],"<br>"
  #print "[ruler.py] masses want",minvalue,"<br>"
  if Range[0] >=0:
    minvalue=Range[0]
  if Range[1] >=0:
    maxvalue=Range[1]

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
    t.DrawLatex(x,y-.01,_pprint(name))
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
    if not formats.has_key(i): formats[i]=False

  if formats["pdf"]:
    #print "[ruler.py] creating %s.pdf" % outputfile
    _execute ( "epspdf %s.eps %s.pdf" % ( tmpf, outputfile ) )
  if formats["png"]:
    formats["eps"]=True
    # print "[ruler.py] creating and cropping %s.png" % outputfile
    crop=""
    if True and not printmass:
      crop="-crop 270x1200+0+0"
    _execute ( "convert %s %s.eps %s.png" % ( crop, tmpf, outputfile ) )
  if formats["eps"]:
    #print "[ruler.py] creating %s.eps" % output
    _execute ( "cp %s.eps %s.eps" % (tmpf, outputfile ) )

  os.unlink ( tmpf )
  
if __name__ == "__main__":
  import argparse, types
  import setPath
  from smodels_tools import SModelSTools
  argparser = argparse.ArgumentParser(description='Draws a "ruler-plot", i.e. particles arranged by their masses. See http://smodels.hephy.at/images/example_ruler.png.')
  #argparser.add_argument ( '-i', '--input',
  #        help='input masses text file name', type=types.StringType, default='@@installdir@@etc/example_masses.txt' )
  argparser.add_argument('inputfile', type=types.StringType, nargs=1,
                    help='input masses text file name, for an example see "etc/example_masses.txt". "@@installdir@@" will be replaced with the installation directory of smodels-tools.')
  argparser.add_argument ( '-m', '--min',
          help='minimal mass, -1 for automatic mode', type=types.IntType, default=-1 )
  argparser.add_argument ( '-M', '--max',
          help='maximum mass, -1 for automatic mode', type=types.IntType, default=-1 )
  argparser.add_argument ( '-o', '--output',
          help='output file name', type=types.StringType, default='ruler' )
  argparser.add_argument ( '-p', '--pdf', help='produce pdf', action='store_true' )
  argparser.add_argument ( '-e', '--eps', help='produce (=keep) eps', action='store_true' )
  argparser.add_argument ( '-P', '--png', help='produce png', action='store_true' )
  argparser.add_argument ( '-mass', '--masses', help='write masses', action='store_true' )
  args=argparser.parse_args()
  Range=[args.min,args.max]
  formats= { "pdf":args.pdf, "eps":args.eps, "png":args.png }

  inputfile=args.inputfile[0].replace("@@installdir@@",SModelSTools.installDirectory() )
  draw ( inputfile, args.output, Range, formats, args.masses )

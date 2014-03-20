#!/usr/bin/python

import ROOT, pickle, os, math, sys, tempfile

def squarkname ( Type, postfix ):
  ret="#tilde{%s}" % Type
  if len(postfix)>0:
    ret+="_{%s}" % postfix
  return ret

def draw ( input, output, keys, Range, formats, printmass=False ):

  f=open( input )
  #pmasses=pickle.load(f)
  pmasses=eval(f.readline())
  f.close()

  keys=keys.split(":")
  masses=pmasses
  #print "masses=",masses,"<br>"
  for (key,value) in masses.items():
    #print "key,value=",key,value,"<br>"
    masses[key]=abs(value)
  for k in keys:
    if len(k): 
      if not masses.has_key(int(k)):
        print "[ruler.py] we dont have masses for key",k
        sys.exit(0)
      else:
        masses=masses[int(k)]

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

  ## print masses

  def color ( name ):
    if name[:4]=="~chi": return ROOT.kGreen+2
    if name[:4]=="~tau": return ROOT.kOrange+2
    if name[:3]=="~mu": return ROOT.kOrange+2
    if name[:3]=="~nu": return ROOT.kOrange+2
    if name=="~g": return ROOT.kRed
    if name[:2]=="~q": return ROOT.kBlue+2
    if name[:2]=="~u": return ROOT.kBlue+2
    if name[:2]=="~d": return ROOT.kBlue+2
    if name[:2]=="~c": return ROOT.kBlue+2
    if name[:2]=="~s": return ROOT.kBlue+2
    if name[:2]=="~t": return ROOT.kBlue+1
    if name[:2]=="~b": return ROOT.kBlue+1
    if name[:2]=="~e": return ROOT.kOrange+2
    if name[:2]=="~l": return ROOT.kOrange+2
    return ROOT.kBlack

  def pprint ( name ):
    if name=="A0": return "a^{0}"
    if name=="A1": return "a^{1}"
    if name=="H+": return "h^{#pm}"
    if name=="Hp": return "h^{#pm}"
    if name=="H2": return "h^{3}"
    if name=="H": return "h^{2}"
    if name=="h": return "h^{1}"
    if name.find("~")>=0:
      if name=="~e": return "#tilde{e}"
      if name=="~g": return "#tilde{g}"
      if name=="~mu": return "#tilde{#mu}"
      if name=="~mu_L": return "#tilde{#mu}_{L}"
      if name=="~mu_R": return "#tilde{#mu}_{R}"
      if name=="~e_L": return "#tilde{e}_{L}"
      if name=="~e_R": return "#tilde{e}_{R}"
      if name=="~tau_L": return "#tilde{#tau}_{L}"
      if name=="~tau_R": return "#tilde{#tau}_{R}"
      if name=="~chi20": return "#tilde{#chi}^{0}_{2}"
      if name=="~chi30": return "#tilde{#chi}^{0}_{3}"
      if name=="~chi40": return "#tilde{#chi}^{0}_{4}"
      if name=="~chi50": return "#tilde{#chi}^{0}_{5}"
      if name=="~chi10": return "#tilde{#chi}^{0}_{1}"
      if name=="~chi1+": return "#tilde{#chi}^{+}_{1}"
      if name=="~chi2+": return "#tilde{#chi}^{+}_{2}"
      if name=="~chi3+": return "#tilde{#chi}^{+}_{3}"
      if name=="~chi4+": return "#tilde{#chi}^{+}_{4}"
      if name.find("~nu_e")==0: return "#tilde{#nu}_{e}"
      if name.find("~nu_mu")==0: return "#tilde{#nu}_{#mu}"
      if name.find("~nu_tau")==0: return "#tilde{#nu}_{#tau}"
      if name.find("~d")==0: return squarkname("d",name[2:])
      if name.find("~u")==0: return squarkname("u",name[2:])
      if name.find("~s")==0: return squarkname("s",name[2:])
      if name.find("~c")==0: return squarkname("c",name[2:])
      if name.find("~t")==0: return squarkname("t",name[2:])
      if name.find("~b")==0: return squarkname("b",name[2:])

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
    return name

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
    col=color (name )
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
    t.DrawLatex(x,y-.01,pprint(name))
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

  c1.Print(tmpf+".eps")

  if formats["pdf"]:
    #print "[ruler.py] creating %s.pdf" % output
    os.system ( "epspdf %s.eps %s.pdf" % ( tmpf, output ) )
  if formats["png"]:
    formats["eps"]=True
    # print "[ruler.py] creating and cropping %s.png" % output
    crop=""
    if True and not printmass:
      crop="-crop 270x1200+0+0"
    os.system ( "convert %s %s.eps %s.png" % ( crop, tmpf, output ) )
  if formats["eps"]:
    #print "[ruler.py] creating %s.eps" % output
    os.system ( "cp %s.eps %s.eps" % (tmpf, output) )

  os.unlink ( tmpf )
  
if __name__ == "__main__":
  import argparse, types
  argparser = argparse.ArgumentParser(description='Draws a "ruler", particles arranged by their masses')
  argparser.add_argument ( '-i', '--input',
          help='input masses text file name', type=types.StringType, default='' )
  argparser.add_argument ( '-m', '--min',
          help='minimal mass, -1 for auto mode', type=types.IntType, default=-1 )
  argparser.add_argument ( '-M', '--max',
          help='maximum mass, -1 for auto mode', type=types.IntType, default=-1 )
  argparser.add_argument ( '-o', '--output',
          help='output file name', type=types.StringType, default='ruler' )
  argparser.add_argument ( '-k', '--keys',
          help='input pickle file name', type=types.StringType, default='' )
  argparser.add_argument ( '-p', '--pdf', help='produce pdf', action='store_true' )
  argparser.add_argument ( '-e', '--eps', help='produce (=keep) eps', action='store_true' )
  argparser.add_argument ( '-P', '--png', help='produce png', action='store_true' )
  argparser.add_argument ( '-mass', '--masses', help='write masses', action='store_true' )
  args=argparser.parse_args()
  Range=[args.min,args.max]
  formats= { "pdf":args.pdf, "eps":args.eps, "png":args.png }

  draw ( args.input, args.output, args.keys, Range, formats, args.masses )

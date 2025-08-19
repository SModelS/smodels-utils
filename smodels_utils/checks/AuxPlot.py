#!/usr/bin/env python3

from __future__ import print_function

import os,sys,copy
from ROOT import TTree,TColor,TCanvas,TF1,TGraph,Double,TFile,gDirectory,TNamed
from scipy import interpolate
from math import sqrt

Var_dic = {"DM_mass" : "m_{DM} (GeV)", "sigv" : "#LT#sigma_{ann}.v#GT (cm^{3}/s)",
           "MScal" : "m_{DM} (GeV)", "MH0" : "m_{DM} (GeV)", "MT0" : "m_{DM} (GeV)"}
Var_dic.update({"SSWW" : "#xi#xi #rightarrow W^{+} W^{-}", "SSWpWm" : "#xi#xi #rightarrow W^{+} W^{-}",
           "SSZZ" : "#xi#xi #rightarrow Z Z",
           "SSAA" : "#xi#xi #rightarrow #gamma #gamma","SSbb" : "#xi#xi #rightarrow b #bar{b}",
           "SScc" : "#xi#xi #rightarrow c #bar{c}", "SStt" : "#xi#xi #rightarrow t #bar{t}",
           "SSHH" : "#xi#xi #rightarrow h h",
           "H0H0bb" : "H^{0}H^{0} #rightarrow b #bar{b}", "H0HpAWp" : "H^{0}H^{+} #rightarrow #gamma W^{+}",
           "H0H0cc" : "H^{0}H^{0} #rightarrow c #bar{c}", "H0A0ss" : "H^{0}A^{0} #rightarrow s #bar{s}",
           "H0H0WpWm" : "H^{0}H^{0} #rightarrow W^{+} W^{-}", "H0H0ZZ" : "H^{0}H^{0} #rightarrow Z Z",
           "H0A0dd" : "H^{0}A^{0} #rightarrow d #bar{d}", "H0H0tt" : "H^{0}H^{0} #rightarrow t #bar{t}",
           "A0A0WpWm" : "A^{0}A^{0} #rightarrow W^{+} W^{-}", "H0H0HH" : "H^{0}H^{0} #rightarrow h h",
           "A0A0bb" : "A^{0}A^{0} #rightarrow b #bar{b}", "HpHmtt" : "H^{+}H^{-} #rightarrow t #bar{t}",
           "H0A0bb" : "H^{0}A^{0} #rightarrow b #bar{b}",
           "T0T0bb" : "T^{0}T^{0} #rightarrow b #bar{b}", "T0HpAWp" : "T^{0}T^{+} #rightarrow #gamma W^{+}",
           "T0T0cc" : "T^{0}T^{0} #rightarrow c #bar{c}", "T0T0WpWm" : "T^{0}T^{0} #rightarrow W^{+} W^{-}", "T0T0ZZ" : "T^{0}T^{0} #rightarrow Z Z",
           "T0T0tt" : "T^{0}T^{0} #rightarrow t #bar{t}", "T0T0HH" : "T^{0}T^{0} #rightarrow h h",
           "TpTmtt" : "T^{+}T^{-} #rightarrow t #bar{t}", "TpTpWpWp" : "T^{+}T^{+} #rightarrow W^{+} W^{+}",
           "TpTmWpWm" : "T^{+}T^{-} #rightarrow W^{+} W^{-}", "T0TpZWp" : "T^{0}T^{+} #rightarrow Z W^{+}",
           "leff" : "#lambda_{#xih}^{RD}","lbar" : "#bar{#lambda}", "|lbar|" : "|#bar{#lambda}|",
           "H_inv" : "BR(h #rightarrow inv.)", "PAMELAbb" : "#LT#sigma.v#GT(#bar{b}b)",
           "PAMELAWW" : "#LT#sigma.v#GT(W^{+}W^{-})",
           "Fermibb" : "#LT#sigma.v#GT(#bar{b}b) (Fermi)",
           "FermiWW" : "#LT#sigma.v#GT(W^{+}W^{-}) (Fermi)", "|ad1|" : "|a_{d1}|",
           "|lbar2|" : "|#lambda_{#xih}^{DD}|", "lbar2" : "#lambda_{#xih}^{DD}"
           })

Exp_dic = {'leff' : "GetLambdas(TREENAME,model)[1]",
           'lbar' : "GetLambdas(TREENAME,model)[0]",
           'lbar2' : "GetLambdas(TREENAME,model)[2]",
           "|lbar|" : "abs(GetLambdas(TREENAME,model)[0])", "|ad1|" : "abs(GetValue(TREENAME,\'ad1\',model))",
           "|lbar2|" : "abs(GetLambdas(TREENAME,model)[2])",
           "|d4|" : "abs(GetValue(TREENAME,\'d4\',model))"}

EXTPAR_dic = {'1' : 'MG1','2' : 'MG2','3' : 'MG3','11' : 'At','12' : 'Ab','13' : 'Al','23' : 'mu','26' : 'MH3','31' : 'Ml1','32' : 'Ml2','33' : 'Ml3','34' : 'Mr1','35' : 'Mr2','36' : 'Mr3','41' : 'Mq1','42' : 'Mq2','43' : 'Mq3', '44' : 'Mu1','45' : 'Mu2','46' : 'Mu3','47' : 'Md1','48' : 'Md2','49' : 'Md3'}

MINPAR_dic = {'3' : 'tanb'}

MassPDG_dic = {'24' : 'W_mass','25' : 'h_mass','35' : 'H_mass','36' : 'H3_mass','37' : 'Hp_mass','5' : 'b_mass'}

SMS_dic = {'TChiChipmSlepL' : '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} #tilde{l}^{#pm}#nu,l^{#pm}#tilde{#nu})#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} #tilde{l}^{#pm}l^{#mp},#nu#tilde{#nu})','TChiChipmSlepStau' : '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} #tilde{#tau}^{#pm}#nu)#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} #tilde{l}^{#pm}l^{#mp})','TChiChipmStauStau' : '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} #tilde{#tau}^{#pm}#nu)#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} #tilde{#tau}^{#pm}#tau^{#mp})','TChiWZ' :  '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} W^{#pm}#tilde{#chi}_{1}^{0})#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} Z#tilde{#chi}_{1}^{0})','TChiWZon' :   '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} W^{#pm}#tilde{#chi}_{1}^{0})#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} Z#tilde{#chi}_{1}^{0})','TChiWZoff' :   '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} W^{#pm}#tilde{#chi}_{1}^{0})#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} Z#tilde{#chi}_{1}^{0})', 'TSlepSlep' : '#tilde{l}^{+}#tilde{l}^{-},#tilde{l} #scale[0.8]{#rightarrow} l#tilde{#chi}_{1}^{0}','T1bbbb' : '#tilde{g}#tilde{g},#tilde{g} #scale[0.8]{#rightarrow} bb#tilde{#chi}_{1}^{0}','T1tbtb' : '#tilde{g}#tilde{g}, #tilde{g} #scale[0.8]{#rightarrow} tb#tilde{#chi}_{1}^{#pm}','T1tttt' : '#tilde{g}#tilde{g}, #tilde{g} #scale[0.8]{#rightarrow} tt#tilde{#chi}_{1}^{0}','T2' : '#tilde{q}#tilde{q}, #tilde{q} #scale[0.8]{#rightarrow} q#tilde{#chi}_{1}^{0}','T2bb' : '#tilde{b}#tilde{b}, #tilde{b} #scale[0.8]{#rightarrow} b#tilde{#chi}_{1}^{0}','T2tt' : '#tilde{t}#tilde{t}, #tilde{t} #scale[0.8]{#rightarrow} t#tilde{#chi}_{1}^{0}','T5WW' : '#tilde{g}#tilde{g}, #tilde{g} #scale[0.8]{#rightarrow} qq#tilde{#chi}_{1}^{#pm}','T6WW' : '#tilde{q}#tilde{q}, #tilde{q} #scale[0.8]{#rightarrow} q#tilde{#chi}_{1}^{#pm}','T6bbWW' : '#tilde{t}#tilde{t}, #tilde{t} #scale[0.8]{#rightarrow} b#tilde{#chi}_{1}^{#pm}','T6bbWWoff' : '#tilde{t}#tilde{t}, #tilde{t} #scale[0.8]{#rightarrow} b#tilde{#chi}_{1}^{#pm}','T5tttt' : '#tilde{g}#tilde{g}, #tilde{g} #scale[0.8]{#rightarrow} t#tilde{t}_{1}','T6bbZZ' : '#tilde{b}#tilde{b}, #tilde{b} #scale[0.8]{#rightarrow} b#tilde{#chi}_{2}^{0}','T6ttWW' : '#tilde{b}#tilde{b}, #tilde{b} #scale[0.8]{#rightarrow} t#tilde{#chi}_{1}^{#pm}','T1' : '#tilde{g}#tilde{g}, #tilde{g} #scale[0.8]{#rightarrow} qq#tilde{#chi}_{1}^{0}', 'TChiChipmStauL' : '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} #tilde{#tau}^{#pm}#nu_{#tau},#tau^{#pm}#tilde{#nu}_{#tau})#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} #tilde{#tau}^{#pm}l^{#mp},#nu#tilde{#nu}_{#tau})','TChipChimSlepSnu' : '#tilde{#chi}_{1}^{#pm} #tilde{#chi}_{1}^{#pm} #scale[0.8]{#rightarrow} l #nu l #nu','TChipChimStauSnu' : '#tilde{#chi}_{1}^{#pm} #tilde{#chi}_{1}^{#pm} #scale[0.8]{#rightarrow} #tau #tau #nu_{#tau} #nu_{#tau}','TChiChiSlepSlep' : '#tilde{#chi}_{2}^{0} #tilde{#chi}_{3}^{0} #scale[0.8]{#rightarrow} 4l','TChiChipmHW' : '#tilde{#chi}_{1}^{#pm}(#scale[0.8]{#rightarrow} W^{#pm}#tilde{#chi}_{1}^{0})#tilde{#chi}_{2}^{0}(#scale[0.8]{#rightarrow} h#tilde{#chi}_{1}^{0})', 'T2bbWW' : '#tilde{t}#tilde{t}, #tilde{t} #scale[0.8]{#rightarrow} bW#tilde{#chi}_{1}^{0}'}

GluinoTops = ['T1', 'T5tttt', 'T1bbbb', 'T5WW', 'T1tttt','T1tbtb']
SquarkTops = ['T2','T6WW']
StopTops = ['T2tt','T6bbWW']
SbotTops = ['T6ttWW', 'T2bb', 'T6bbZZ']
EWinoTops = ['TChiWZ', 'TChiChipmSlepL', 'TChiChipmSlepStau']
SlepTops = ['TSlepSlep']


def infiles(argv):
  filename = argv[1]
  if len(argv) > 2:
    friends = argv[2:]
  else: friends = []

  goodfriends = []
  for friend in friends:
    if os.path.isfile(friend): goodfriends.append(friend)
    elif os.path.isdir(friend):
      dirfiles = os.listdir(friend)
      for f in dirfiles:
        fname = friend+f
        if not os.path.isfile(fname): continue
        if fname[-5:] == '.root' and fname != filename: goodfriends.append(fname)

  return filename,goodfriends

def getTree(gDirectory,friends=[],verbose=False):

#Get Trees:
  objs =  gDirectory.GetListOfKeys()
  trees = []
  for ob in objs:
    Tob = ob.ReadObj()
    if type(Tob) == type(TTree()):
      trees.append(Tob)

  if len(trees) <= 0:
    print ( "No trees found in file" )
    sys.exit()
  elif len(trees) > 1:
    pstr = "More than one tree found, specify which one to use ("
    for tree in trees:
      pstr += f"{tree.GetName()},"
    pstr += ")"
    usetree = raw_input(pstr)
    tree = gDirectory.Get(usetree)
  else:
    tree = trees[0]

  for ifriend,friend in enumerate(friends):
    print ( "Adding friend",friend )
    tree.AddFriend(f"friend{ifriend!s} = {tree.GetName()!s}",friend)

#Get Branches and Leaves (variables):
  branches = tree.GetListOfBranches()
  leaves = tree.GetListOfLeaves()
  lnames = [leaf.GetName() for leaf in leaves]

#Get Input parameters:
  inputpars = {}
  for br in branches:
    if br.GetName().lower() != "input": continue
    for leaf in br.GetListOfLeaves():
      lname = leaf.GetName()
      inputpars.update({lname : [tree.GetMinimum(lname),tree.GetMaximum(lname)]})

  if verbose:
    print ( "Nevts = ",tree.GetEntries() )
    print ( "Input parameters and range:" )
    for key in inputpars.keys():
      print ( key,inputpars[key] )

  return tree,lnames,inputpars

#Use Var_dic to create latex-compliant names for the leaves.
#If Var_dic does not contain the leaf name, use the own name:
def GetVarNames(allvars,useDic=None):

  dic = Var_dic
  if useDic: dic = dict(useDic.items() + Var_dic.items())
  varnames = {}
  for vname in allvars:
    if dic.has_key(vname):
      varnames.update({vname : dic[vname]})
    else:
      varnames.update({vname : vname})

  return varnames

#Check if variables in AllowedRange.keys() have their values in the allowed range
def GetExcluded(AllowedRange,tree,model='singlet'):

  excluded = {}

  for exc,interval in AllowedRange.items():
    try:
      if interval[0] <= GetValue(tree,exc,model) <= interval[1]:
        excluded[exc] = False
      else:
        excluded[exc] = True
    except:
      pass

  return excluded


def GetValue(tree,x,model='singlet'):

  if hasattr(tree,x): return getattr(tree,x)
  if x in Exp_dic.keys():
    exp = Exp_dic[x]
    exp = exp.replace("TREENAME","tree")
    return eval(exp)
  else:
    print ( "[GetValue]: Unknown variable",x )
    sys.exit()



def Default(obj,Type):

  if Type == "TCanvas":
    obj.SetLeftMargin(0.1097891)
    obj.SetRightMargin(0.02700422)
    obj.SetTopMargin(0.02796053)
    obj.SetBottomMargin(0.14796053)
    obj.SetFillColor(0)
    obj.SetBorderSize(0)
    obj.SetFrameBorderMode(0)
  elif "TGraph" in Type or "TH" in Type:
    obj.GetYaxis().SetTitleFont(132)
    obj.GetYaxis().SetTitleSize(0.075)
    obj.GetYaxis().CenterTitle(True)
    obj.GetYaxis().SetTitleOffset(1.15)
    obj.GetXaxis().SetTitleFont(132)
    obj.GetXaxis().SetTitleSize(0.075)
    obj.GetXaxis().CenterTitle(True)
    obj.GetXaxis().SetTitleOffset(1.2)
    obj.GetYaxis().SetLabelFont(132)
    obj.GetXaxis().SetLabelFont(132)
    obj.GetYaxis().SetLabelSize(0.055)
    obj.GetXaxis().SetLabelSize(0.06)
    if "TGraph2D" in Type or "TH2" in Type:
      obj.GetZaxis().SetTitleFont(132)
      obj.GetZaxis().SetTitleSize(0.06)
      obj.GetZaxis().CenterTitle(True)
      obj.GetZaxis().SetTitleOffset(0.7)
      obj.GetZaxis().SetLabelFont(132)
      obj.GetZaxis().SetLabelSize(0.05)
  elif "Leg" in Type:
   obj.SetBorderSize(1)
   obj.SetMargin(0.35)
   obj.SetTextFont(132)
   obj.SetTextSize(0.05)
   obj.SetLineColor(1)
   obj.SetLineStyle(1)
   obj.SetLineWidth(1)
   obj.SetFillColor(0)
   obj.SetFillStyle(1001)


def Print(canvas,prefix,hasSMS):
  filename = prefix
  if hasSMS:
    addname = hasSMS.rstrip(".root")
    while addname.count("_") > 0:
      addname = addname[addname.index("_")+1:]
    filename += f"_{addname}"
  filename += ".eps"
  canvas.Print(filename)

def printInput(tree,inputpars):

  for key in inputpars.keys():
    print ( key,getattr(tree,key) )


def set_palette(gStyle,name="none", ncontours=999):
    """Set a color palette from a given RGB list
    stops, red, green and blue should all be lists of the same length
    see set_decent_colors for an example"""

    from array import array

    if name == "gray" or name == "grayscale":
        stops = [0.00, 0.34, 0.61, 0.84, 1.00]
        red   = [1.00, 0.84, 0.61, 0.34, 0.00]
        green = [1.00, 0.84, 0.61, 0.34, 0.00]
        blue  = [1.00, 0.84, 0.61, 0.34, 0.00]
    else:
        # default palette, looks cool
        stops = [0.00, 0.34, 0.61, 0.84, 1.00]
        red   = [0.00, 0.00, 0.87, 1.00, 0.51]
        green = [0.00, 0.81, 1.00, 0.20, 0.00]
        blue  = [0.51, 1.00, 0.12, 0.00, 0.00]

    s = array('d', stops)
    r = array('d', red)
    g = array('d', green)
    b = array('d', blue)

    npoints = len(s)
    TColor.CreateGradientColorTable(npoints, s, r, g, b, ncontours)
    gStyle.SetNumberContours(ncontours)

def getContours(gROOT,vals,hist,fit=None):
    """Get contour graphs from a histogram with contour values vals"""
    from array import array

    res = {}
    canv = TCanvas("getContour_canvas","getContour_canvas",0,0,500,500)
    canv.cd()
    h2 = hist.Clone()
    contours = array('d',vals)
    h2.SetContour(len(vals),contours)
    h2.Draw("CONT Z LIST")
    canv.Update()
    conts = gROOT.GetListOfSpecials().FindObject("contours")
    for ival,val in enumerate(vals):
        contLevel = conts.At(ival)
        res[val] = contLevel.First()
        for cont in contLevel:
            if cont.GetN() > res[val].GetN(): res[val] = cont   #Get the contour wiht highest number of points

    if fit:
        f1 = TF1("f1",fit,0.,1000.)
        for val in vals:
            curv = res[val].Clone()
            curv.Sort()
            xmin = curv.GetX()[0]
            xmax = curv.GetX()[curv.GetN()-1]
            f1.SetMinimum(xmin)
            f1.SetMaximum(xmax)
            curv.Fit(f1)
            fit = TGraph(curv.FindObject("f1"))
            res[val] = fit.Clone()

    canv.Clear()

    return res

def getData(fname,Rmax=1.,condmax=0.001):
  infile = open(fname,'r')
  data = infile.read()
  pts = data[:data.find('#END')-1].split('\n')
  not_tested = TGraph()
  exc = TGraph()
  allow = TGraph()
  not_cond = TGraph()

  xv = []
  yv = []
  limv = []
  condv = []
  resv = []
  for pt in pts:
    x,y,res,lim,cond,tot = pt.split()
    R = float(eval(res))/float(eval(lim))
    if eval(res) < 0.: continue
    if cond == 'None': cond = '0.'
    x = eval(x)
    y = eval(y)
    lim = eval(lim)
    cond = eval(cond)
    res = eval(res)
    xv.append(x)
    yv.append(y)
    limv.append(lim)
    condv.append(cond)
    resv.append(res)
    if cond > condmax: not_cond.SetPoint(not_cond.GetN(),x,y)
    if R < 0.:
      not_tested.SetPoint(not_tested.GetN(),x,y)
    elif R >= Rmax:
      exc.SetPoint(exc.GetN(),x,y)
    elif R < Rmax:
      allow.SetPoint(allow.GetN(),x,y)
    else:
      print ( 'Unknown R value',R )
      sys.exit()

  infile.close()
  return {'exc' : exc, 'not_tested' : not_tested, 'not_cond' : not_cond, 'allow' : allow, 'xv' : xv, 'yv' : yv, 'resv' : resv, 'limv' : limv, 'condv' : condv}

def getEnvelope(excluded,consecutive_bins=3):

  exc_curve = TGraph()
  exc = copy.deepcopy(excluded)
  exc.Sort()
  x1,y1 = Double(), Double()
  exc.GetPoint(0,x1,y1)
  yline = []
  for ipt in range(exc.GetN()+1):
    x,y = Double(), Double()
    dmin = 0.
    if ipt < exc.GetN(): exc.GetPoint(ipt,x,y)
    if ipt != exc.GetN() and x == x1: yline.append(y)
    else:
      yline = sorted(yline,reverse=True)
      dy = [abs(yline[i]-yline[i+1]) for i in range(len(yline)-1)]
      if len(yline) <= 3 or exc_curve.GetN() == 0:
        newy = max(yline)
        if len(dy) > 2: dmin = min([abs(yline[i]-yline[i+1]) for i in range(len(yline)-1)])
      else:
        newy = max(yline)
#        dmin = min(dy)
        dmin = sum(dy)/float(len(dy))
        for iD in range(len(dy)-1):
          if dy[iD] <= dmin and dy[iD+1] <= dmin:
            newy = yline[iD]
            break
      exc_curve.SetPoint(exc_curve.GetN(),x1,newy+dmin/2.)
      x1 = x
      yline = [y]

  x2,y2 = Double(), Double()
  exc_curve.GetPoint(exc_curve.GetN()-1,x2,y2)
  exc_curve.SetPoint(exc_curve.GetN(),x2,0.)  #Close exclusion curve at zero
  return exc_curve


def getMetadata(filename,tags):
  infile = open(filename,'r')
  data = infile.read()
  info = data[data.find('#END'):].split('\n')
  metadata = {}
  for tag in tags: metadata[tag] = None
  if len(info) > 0:
    for line in info:
      for tag in tags:
        if tag in line:
          if not metadata[tag]: metadata[tag] = []
          entry = line.lstrip(f"{tag} :").rstrip()
          if ':' in entry: entry = entry.split(':')
          metadata[tag].append(entry)

  infile.close()
  return metadata


def getRootPlots(metadata):
  plots = {}
  if metadata['Root file'] and os.path.isfile(metadata['Root file'][0]):
    rootfile = TFile(metadata['Root file'][0],"read")
    objs =  gDirectory.GetListOfKeys()
    for ob in objs:
      add = False
      Tob = ob.ReadObj()
      if type(Tob) != type(TGraph()): continue
      if metadata['Root tag']:
        for rootTag in metadata['Root tag']:
          Tag = rootTag
          if type(Tag) == type([]) and len(Tag) > 1: Tag = Tag[0]
          if Tag == ob.GetName():  add = rootTag
      else:
        add = 'Official Exclusion'
      if add:
        if type(add) == type([]): add = add[1]
        plots[add] = copy.deepcopy(Tob)

  return plots

def convertLabels(indic,use_dic=None,exclusive=False):

  outdic = {}
  if use_dic:
    myLabels = globals()[use_dic]
  else:
    myLabels = EXTPAR_dic
    myLabels.update(MINPAR_dic)
    myLabels.update(MassPDG_dic)
    myLabels.update(Observables_dic)
  for key in indic.keys():
    if str(key) in myLabels: outdic[myLabels[str(key)]] = indic[key]
    elif not exclusive: outdic[str(key)] = indic[key]

  return outdic


def getAnalysesOptions(analyses):

  markers = [20,21,22,23,29]
  colorsA = ['kGreen+1','kMagenta','kMagenta+2','kAzure-6','kMagenta+3','kAzure+2', 'kMagenta-4','kAzure+10','kMagenta-9','kAzure+1','kAzure-7','kAzure-2','kAzure-5']
  colorsB = ['kRed+2','kOrange+1','kPink-2','kRed-5','kOrange-3','kRed-6','kRed-4', 'kOrange+4']
  analyses = list(set(analyses))
  analyses_opts = {}
  allopts = []
  for f in analyses:
    imarker = 0
    icolor = 0
    if 'TChi' in f or 'TSlep' in f: usecolors = colorsB
    else: usecolors = colorsA
    while [usecolors[icolor],markers[imarker]] in allopts:
      if icolor == len(usecolors)-1 and imarker == len(markers)-1:
        print ( 'getAnalysesOptions: Number of analyses exceeded number of possible options' )
        print ( len(analyses),len(markers)*len(colorsA),len(markers)*len(colorsB) )
        print ( f )
        sys.exit()

      icolor += 1
      if icolor >= len(usecolors):
        icolor = 0
        imarker += 1

    Mstyle = markers[imarker]
    Mcolor = usecolors[icolor]
    analyses_opts[f] = {"MarkerStyle" : Mstyle, "MarkerColor" : Mcolor}
    allopts.append([Mcolor,Mstyle])

  return analyses_opts


def checkOrderBy(variable,tree,friends):

  if len(friends) == 0: return True
  varlist = []
  nevts = tree.GetEntries()
  for iev in range(nevts):
    tree.GetEntry(iev)
    var = GetValue(tree,variable)
    if 'file' in variable.lower():
      var = str(var)
      var = var[:var.rfind('.')]
    varlist.append(var)
  for ifriend,friend in enumerate(friends):
    ffriend = TFile(friend)
    tfriend = ffriend.Get(tree.GetName())
    if tfriend.GetEntries() != nevts:
      print ( friend,'and tree number of entries do not match' )
      return False
    for iev in range(nevts):
      tfriend.GetEntry(iev)
      var = GetValue(tfriend,variable)
      if 'file' in variable.lower():
        var = str(var)
        var = var[:var.rfind('.')]
      if var != varlist[iev]:
        print ( friend,'and tree',variable,'do not match at event',iev )
        return False
    tfriend.Delete()
    ffriend.Close()

  return True

def getBestAnalysis(ana_list,sqrts=8.):

  R_best_Good = 0.
  Th_best_Good = 0.
  Cond_best_Good = 0.
  Ana_best_Good = "NONE"
  R_best_Bad = 0.
  Th_best_Bad = 0.
  Cond_best_Bad = 0.
  Ana_best_Bad = "NONE"
  for ana in ana_list:
    if ana['AnalysisSqrts'] != sqrts: continue
    if ana['exptlimit'] <= 0.: continue
    if ana['maxcond'] < 0.2:
      if not R_best_Good or R_best_Good < ana['tval']/ana['exptlimit']:
       R_best_Good = ana['tval']/ana['exptlimit']
       Th_best_Good = ana['tval']
       Cond_best_Good = ana['maxcond']
       Ana_best_Good = f"{ana['AnalysisName']}:{ana['AnalysisTopo']}"
    else:
      if not R_best_Bad or R_best_Bad < ana['tval']/ana['exptlimit']:
       R_best_Bad = ana['tval']/ana['exptlimit']
       Th_best_Bad = ana['tval']
       Cond_best_Bad = ana['maxcond']
       Ana_best_Bad = f"{ana['AnalysisName']}:{ana['AnalysisTopo']}"

  best_dic = {"R_best_Good" : R_best_Good, "Th_best_Good" : Th_best_Good, "Cond_best_Good" : Cond_best_Good, "Ana_best_Good" : Ana_best_Good, "R_best_Bad" : R_best_Bad, "Th_best_Bad" : Th_best_Bad, "Cond_best_Bad" : Cond_best_Bad, "Ana_best_Bad" : Ana_best_Bad}

  return best_dic

def GetCurve(datafile,kind='linear',fillvalue=0.):
    """ Reads data file with x,y values and returns the interpolation function"""

    fdata = open(datafile,'r')
    xdata,ydata = [],[]
    for l in fdata.readlines():
        l = l.split()
        if len(l) != 2:
            print ( "Error reading",datafile,"in line",l )
            sys.exit()
        xdata.append(eval(l[0]))
        ydata.append(eval(l[1]))

    data = [[xdata[ipt],ydata[ipt]] for ipt,pt in enumerate(xdata)]
    data = sorted(data)
    xdata = [x[0] for x in data]
    ydata = [x[1] for x in data]

    fdata.close()
    func = interpolate.interp1d(xdata,ydata,kind,fill_value=fillvalue)
    return func

def GetLambdas(tree,model):
    """Compute the effective lambda  couplings depending on the model"""

    v = 246.2
    fval =  GetValue(tree,"Lamf")
    if model == 'singlet':
        MScal = GetValue(tree,"MScal")
        lam3 = GetValue(tree,"lam3")
        l3p = GetValue(tree,"l3p")
        lbar = lam3*(1. + l3p*v**2/fval**2)
        leff = lbar/2. - 4.*GetValue(tree,"ad1")*MScal**2/fval**2
        lbar2 = lbar
    elif model == 'doublet':
        MH0 = GetValue(tree,"MH0")
        MHc = GetValue(tree,"MHc")
        MA0 = GetValue(tree,"MA0")
        MU22 = GetValue(tree,"MU22")
        lam3p = GetValue(tree,"lam3p")
        lam4p = GetValue(tree,"lam4p")
        lam5p = GetValue(tree,"lam5p")
        l3 = 4.*fval**2*(MHc**2 - MU22)/(2.*fval**2*v**2 + lam3p*v**4)
        l5 = 2.*fval**2*(MH0**2 - MA0**2)/(2.*fval**2*v**2 + lam5p*v**4)
        l4 = (-l5*lam5p*v**4 + fval**2*(4.*MH0**2 - 4.*MHc**2 - 2.*l5*v**2))/(2.*fval**2*v**2 + lam4p*v**4)
        lbar = l3*(1. + lam3p*v**2/fval**2) + l4*(1. + lam4p*v**2/fval**2) + l5*(1. + lam5p*v**2/fval**2)
        lbar2 = lbar/2. -2.*GetValue(tree,"ad3")*MH0**2/fval**2
        leff = lbar/2.
        leff += -(MH0**2/fval**2)*(GetValue(tree,"ad1")+2.*GetValue(tree,"ad2")+2.*GetValue(tree,"ad3"))
    elif model == 'triplet':
        MT0 = GetValue(tree,"MT0")
        lam3 = GetValue(tree,"l3")
        l5 = GetValue(tree,"l5")
        l3p = GetValue(tree,"lam3p")
        lbar = lam3*(1. + l3p*v**2/fval**2) + 4.*l5*v**2/fval**2
        leff = lbar/2. - GetValue(tree,"ad1")*MT0**2/fval**2
        lbar2 = lbar

    return lbar,leff,lbar2


def smallPars(tree,model):
    """Checks if the effective parameters suppressed by 1/F^2 are always
    smaller than 1.
    """

    #Higgs constraints:
    a2H = GetValue(tree,'a2H')
    lamH6 = GetValue(tree,'lamH6')
    MH = GetValue(tree,'MH')
    c4 = GetValue(tree,'c4')
    fval = GetValue(tree,'Lamf')
    v = 246.2
    ren = 1./sqrt(1+2.*a2H*v**2/fval**2)
    lam1 = v**(-2)*ren**(-2)*(MH**2 - 2.*lamH6*v**4/fval**2)/2.
    if abs(lam1*lamH6) > 1.: return False
    if abs(c4) > 1.: return False

    #Singlet constraints:
    if model == 'singlet':
        l3p = GetValue(tree,'l3p')
        ad1 = GetValue(tree,'ad1')
        d4 = GetValue(tree,'d4')
        if abs(l3p) > 1.: return False
        if abs(ad1) > 1.: return False
        if abs(d4) > 1.: return False
    elif model == 'doublet':
        MH0 = GetValue(tree,"MH0")
        MHc = GetValue(tree,"MHc")
        MA0 = GetValue(tree,"MA0")
        MU22 = GetValue(tree,"MU22")
        lam3p = GetValue(tree,"lam3p")
        lam4p = GetValue(tree,"lam4p")
        lam5p = GetValue(tree,"lam5p")
        ad1 = GetValue(tree,'ad1')
        ad2 = GetValue(tree,'ad2')
        ad3 = GetValue(tree,'ad3')
        ad4 = GetValue(tree,'ad4')
        d4 = GetValue(tree,'d4')
        d6 = GetValue(tree,'d6')
        if abs(lam3p) > 1.: return False
        if abs(lam4p) > 1.: return False
        if abs(lam5p) > 1.: return False
        if abs(ad1) > 1.: return False
        if abs(ad2) > 1.: return False
        if abs(ad3) > 1.: return False
        if abs(ad4) > 1.: return False
        if abs(d4) > 1.: return False
        if abs(d6) > 1.: return False
    elif model == 'triplet':
        l3p = GetValue(tree,'lam3p')
        l4 = GetValue(tree,'l4')
        l5 = GetValue(tree,'l5')
        ad1 = GetValue(tree,'ad1')
        ad4 = GetValue(tree,'ad4')
        d4 = GetValue(tree,'d4')
        if abs(l3p) > 1.: return False
        if abs(l4) > 1.: return False
        if abs(l5) > 1.: return False
        if abs(ad1) > 1.: return False
        if abs(ad4) > 1.: return False
        if abs(d4) > 1.: return False

    return True


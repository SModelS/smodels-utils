#!/usr/bin/env python

'''
.. module:: prettyDescriptions
   :synopsis: Module to provide some latex-coded strings needed for summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


'''
# ### FIX ME: this is very preliminary => maybe can be replaced completely by functionality located in other modules
# ### FIX ME: Has to be rewritten completely!

# topologies linked to motherparticle:

motherparticle = {
	'g': ['T1', 'T5WW', 'T5WH', 'T1bbbb', 'T1tttt', 'T1tbtb', 'T5tttt'],
	'q': ['T2'],
	'b': ['T2bb', 'T6ttWW'],
	't': ['T2tt', 'T6bbWW', 'T6ttZZ'],
	'c0': ['TChiZZ', 'TChiChiSlepSlep'],
	'cpm': ['TChiWW', 'TChipChimSlepSnu', 'TChipChimStauSnu'],
	'l': ['TSlepSlep'],
	'c0cpm': ['TChiWZ', 'TChiChipmSlepL', 'TChiChipmStauL', 'TChiChipmSlepStau', 'TChiChipmStauStau']
}
	



# pretty name of particle:

prettyParticle = {
	'lsp' : '#tilde{#chi}^{0}_{1}',  # lightesd SUSY particle
	'chargino^pm' : '#tilde{#chi}^{#pm}', #chargino +/- 
	'chargino^mp' : '#tilde{#chi}^{#mp}', #chargino -/+
	'chargino^p' : '#tilde{#chi}^{+}',    #chargino +
	'chargino^m' : '#tilde{#chi}^{-}',    #chargino -
	'neutralino' : '#tilde{#chi}^{0}',    #neutralino
	
	'gravitino':'G',              #gravitino
	'graviton':'#tilde{G}',         #graviton
	'photino':'#tilde{#gamma}',   #photino
	'photon': '#gamma',             #photon
	'gluino': '#tilde{g}',        #gluino
	'gluon':'g',                    #gluon
	'wino' : '#tilde{W}',       #Wino
	'w' : 'W',                  #W
	'wino^p' : '#tilde{W}^{+}', #Wino+
	'w^p' : 'W^{+}',            #W+
	'wino^m' : '#tilde{W}^{-}', #Wino-
	'w^m' : 'W^{-}',            #W-
	'zino' : '#tilde{Z}',       #Zino
	'z' : 'Z',                  #Z
	'higgsino' : '#tilde{H}',       #higgsino
	'higgs' : 'H',                  #higgs
	
	'squark': '#tilde{q}',  #squark
	'quark': 'q',           #quark
	'sup': '#tilde{u}',  #sup
	'up': 'u',           #up
	'sdown': '#tilde{d}',  #sdown
	'down': 'd',           #down
	'scharm': '#tilde{c}',  #scharm
	'charm': 'c',           #charm
	'sstrange': '#tilde{s}',  #sstarnge
	'strange': 's',           #strange
	'stop': '#tilde{t}',  #stop
	'top': 't',           #top
	'sbottom': '#tilde{b}',  #sbottom
	'bottom': 'b',           #bottom
	
	'slepton' : '#tilde{l}',    #slepton
	'lepton' : 'l',             #lepton
	'lepton^pm' : 'l^{#pm}',
	'lepton^p' : 'l^{+}',
	'lepton^m' : 'l^{-}',
	'lepton^mp' : 'l^{#mp}',
	'selectron' : '#tilde{e}',      #selectron
	'electron' : 'e',               #electron
	'smyon' : '#tilde{#mu}',   #smyon
	'muyon' : '#mu',            #myon
	'stauon' : '#tilde{#tau}', #stauon
	'tauon' : '#tilde{#tau}',  #tauon
	
	'sneutrino' : '#tilde{#nu}',            #sneutrino
	'neutrino' : '#nu',                     #neutrino
	'elektron-sneutrino' : '#tilde{#nu}_{e}',      #elektron-sneutrino
	'elektron-neutrino' : '#nu_{e}',               #elektron-neutrino
	'myon-sneutrino' : '#tilde{#nu}_{#mu}',   #myon-sneutrino
	'myon-neutrino' : '#nu_{#mu}',            #myon-neutrino
	'tauon-sneutrino' : '#tilde{#nu}_{#tau}', #tauon-sneutrino
	'tauon-neutrino' : '#nu_{#tau}',          #tauon-neutrino

}

# pretty name of Analyses for summary plots:

prettyAnalysisName = {
	'SUS12028': '0-lep (#alpha_{T})',
	'SUS12024': 'b-jet',
	'SUS13013': '2-lep (SS+b)',
	'SUS13007': '1-lep (#Delta#phi)',
	'SUS13007LS': '1-lep (LS)',
	'SUS13008': '3-lep (3l+b)',
	'SUS13016': '2-lep (OS+b)',
	'SUS13004': '0+1-lep (razor)',
	'SUS13002': '(MultiLepton)',
	'SUS13019': '(MT_{2})',
	'SUS13012': '0-lep (#slash{E}_{T}+H_{T})',
	'SUS13004': '0+1-lep (razor)',
	'SUS13016': '2-lep (OS+b)'
}

# pretty name of decay:

decay = { 'T1': 'gluino  --> quark anti-quark  lsp ' , #tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{1}', 
	'T1bbbb': 'gluino  --> bottom anti-bottom  lsp ', #tilde{g} #rightarrow b#bar{b} #tilde{#chi}^{0}_{1}',
	'T1tttt': 'gluino  --> top anti-top  lsp ', #tilde{g} #rightarrow t#bar{t} #tilde{#chi}^{0}_{1}',
	'T1gg':'gluino  --> quark anti-quark (neutralino --> photon lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow #gamma#tilde{#chi}^{0}_{1})',
	'T1lg':'gluino  --> quark anti-quark (neutralino  --> photon lsp |chargino^pm  --> w lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow#gamma#tilde{#chi}^{0}_{1}|#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
	'T1lnu':'gluino  --> quark anti-quark (chargino^pm --> lepton^pm neutrino  lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm} #rightarrow l^{#pm}#nu #tilde{#chi}^{0}_{1})',
	'T1lh':'gluino  --> quark anti-quark  neutralino neutralino  --> lepton^p lepton^m lsp ' #tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{2},#tilde{#chi}^{0}_{2} #rightarrow l^{+}l^{-}#tilde{#chi}^{0}_{1}',
	#'T2':'#tilde{q} #rightarrow q #tilde{#chi}^{0}_{1}',
	#'T2FVttcc': '#tilde{t} #rightarrow c #tilde{#chi}^{0}_{1}',
    #'T2llnunubb': '#tilde{t} #rightarrow l #nu b #tilde{#chi}^{0}_{1}',
    #'T2bb':'#tilde{b} #rightarrow b #tilde{#chi}^{0}_{1}',
    #'T2bw':'#tilde{t} #rightarrow b (#tilde{#chi}^{#pm}_{1} #rightarrow W #tilde{#chi}^{0}_{1})',
    #'T2ttww': '#tilde{b} #rightarrow tW #tilde{#chi}^{0}_{1}',
    #'T2tt': '#tilde{t} #rightarrow t #tilde{#chi}^{0}_{1}',
    #'T3w': '#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1} |#tilde{#chi}^{0}_{1})',
    #'T3wb':'#tilde{g} #rightarrow b#bar{b}(W)#tilde{#chi}^{0}_{1}',
    #'T3lh':'#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow l^{+}l^{-}#tilde{#chi}^{0}_{1})',
    #'T3tauh':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{2}#rightarrow #tau #tau #tilde{#chi}^{0}_{1} |#tilde{#chi}^{0}_{1})',
    #'T5WW':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
    #'T5wg':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow#gamma#tilde{#chi}^{0}_{1}|#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
    #'T5WH':'#tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1} H#tilde{#chi}^{0}_{1} ',
    #'T5gg':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow #gamma#tilde{#chi}^{0}_{1})',
    #'T5lnu':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm} #rightarrow l^{#pm}#nu #tilde{#chi}^{0}_{1})',
    #'T5ZZ':'#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow Z #tilde{#chi}^{0}_{1})',
    #'T5ZZInc':'#tilde{#chi}^{0}_{2} #rightarrow Z #tilde{#chi}^{0}_{1}',
    #'T5zzgmsb':'#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow Z #tilde{#chi}^{0}_{1})',
    #'T5tttt':'#tilde{g} #rightarrow t(#tilde{t} #rightarrow t#tilde{#chi}^{0}_{1})',
    #'T6ttww': '#tilde{b} #rightarrow tW #tilde{#chi}^{0}_{1}',
    #'T6ttHH': '#tilde{t} #rightarrow tH #tilde{#chi}^{0}_{1}',
    #'T6ttzz': '#tilde{t}_{2} #rightarrow tilde{t}_{1}Z #rightarrow #tilde{#chi}^{0}_{1}t',
    #'T6bbWW':'#tilde{t} #rightarrow b(#tilde{#chi}^{+} #rightarrow W#tilde{#chi}^{0}_{1})',
    #'T6bbZZ':'#tilde{b} #rightarrow bZ #tilde{#chi}^{0}_{1}',
    #'T7btW':'#tilde{g} #rightarrow btW#tilde{#chi}^{0}_{1}',
    #'T7btbtWW':'#tilde{g} #rightarrow b(#tilde{b} #rightarrow t(#tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1}))',
    #'TChiwz':'#tilde{#chi}^{#pm} #tilde{#chi}^{0}_{2} #rightarrow W Z #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1}',
    #'TChizz':'#tilde{#chi}^{0}_{3} #tilde{#chi}^{0}_{2} #rightarrow Z Z #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1}',
    #'TChiSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow l l l #nu #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChiNuSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow l l l #nu #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChiSlepSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChiChipmHW':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1} H#tilde{#chi}^{0}_{1} ',
    #'TChiChipmSlepL':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChiChipmSlepSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChiChipmSlepStau':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow ll#tau #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChiChipmStauStau':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow #tau#tau#tau #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    #'TChipChimSlepSnu':'#tilde{#chi}^{+}#tilde{#chi}^{-} #rightarrow l^{+}l^{-}#nu#nu#tilde{#chi}^{0}_{1}#tilde{#chi}^{0}_{1}',
    #'TSlepSlep':'#tilde{l} #rightarrow l #tilde{#chi}^{0}_{1}'
}

def prettyDecay(topoName):
    if not topoName in decay: return None
    decayString = decay[topoName]
    for key, value in prettyParticle.items():
        decayString = decayString.replace('anti-' + key + ' ','#bar{' + value + '}')
        decayString = decayString.replace(key + ' ',value)
    decayString = decayString.replace('-->','#rightarrow')
    return decayString
        

def decays(topo,plot = 'ROOT', kerning=True, omitleft=False ):
  """ give the pretty decay string for a given topo.
      E.g. T1 -> ~g -> q q ~ch10.
      kerning: means smaller space between > and >
      omitleft means omit everything up to #rightarrow """

  if decay.has_key(topo):
    part = decay[topo]
    if omitleft and part.find("#rightarrow")>-1:
      part=part[part.find("#rightarrow"):]
    if plot=="ROOT":
      return part
    part = '$' + part.replace('#','\\') + '$'
    if kerning:
      part=part.replace(">>",">#kern[-.2]{>}")
    return part
  else:
    return None


#'Hadronic112q':'#tilde{q}_{R} #rightarrow qqqq  #lambda''_{112}',
    #'Leptonic233q':'#tilde{q} #rightarrow qll#nu  #lambda_{233}',
    #'Leptonic122g':'#tilde{g} #rightarrow qll#nu  #lambda_{122}',
    #'SemiLeptonic233g':'#tilde{g} #rightarrow qbt#mu  #lambda'_{233}',,,
    #'SemiLeptonic233q':'#tilde{q} #rightarrow qbt#mu  #lambda'_{233}',
    #'bprime':'b' #rightarrow bZ',
    #'Stop233':'#tilde{t}_{R} #rightarrow #mu#tau#nut  #lambda_{233}',
    #'Leptonic122q':'#tilde{q} #rightarrow qll#nu  #lambda_{122}',
    #'Hadronic112g':'#tilde{g} #rightarrow qqqq  #lambda''_{112}',
    #'Hadronic122g':'#tilde{g} #rightarrow qqqq  #lambda_{122}',
    #'Stop122':'#tilde{t}_{R} #rightarrow #mue#nut  #lambda_{122}',
    #'Stop123':'#tilde{t}_{R} #rightarrow #mu#tau#nut  #lambda_{123}',
    #'Leptonic123g':'#tilde{g} #rightarrow qll#nu  #lambda_{123}',
    #'Leptonic123q':'#tilde{q} #rightarrow qll#nu  #lambda_{123}',
    #'StopLLE122':'#tilde{t}_{R} #rightarrow t#nu_{#mu}e#mu  #lambda_{122}',
    #'StopLLE233':'#tilde{t}_{R} #rightarrow t#nu_{#tau}#mu#tau  #lambda_{233}',
    #'StopLQD233':'#tilde{t}_{R} #rightarrow tbt#mu  #lambda'_{233}',
    
    
    
    
    #'Rstop':'#tilde{t} #rightarrow b#tau  #lambda'_{333}',
    #'Rg3j':'#tilde{g} #rightarrow qqq  #lambda''_{112}',
    #'SemiLeptonic231g':'#tilde{g} #rightarrow qbt#mu  #lambda'_{231}',
    #'SemiLeptonic231q':'#tilde{q} #rightarrow qbt#mu  #lambda'_{231}',
    
    
    #'Gluino113/223':'#tilde{g} #rightarrow qqb  #lambda''_{113/223}',
    #'Gluino323':'#tilde{g} #rightarrow tbs  #lambda''_{323}'
    
dicparticle = { 
     "T1": "#tilde{g}",
     "T1bbbb": "#tilde{g}",
     "T1tttt": "#tilde{g}",
     "T1lg": "#tilde{g}",
     "T1gg": "#tilde{g}",
     "T5gg": "#tilde{g}",
     "T5Wg": "#tilde{g}",
     "T2": "#tilde{q}",
     "T2bb": "#tilde{b}",
     "T2tt": "#tilde{t}",
     "T2ttww": "#tilde{b}",
     "T3w": "#tilde{g}",
     "T3lh": "#tilde{g}",
     "T5zz": "#tilde{g}",
     "T5zzInc": "#tilde{g}", 
     #"T5zzh": "#tilde{g}", 
     #"T5zzl": "#tilde{g}", 
     "T5lnu": "#tilde{g}",
     "T5zzgmsb": "#tilde{g}",
     "T6bbWW": "#tilde{t}", 
     "TChiwz": "#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}",
     #"TChiwz": "#tilde{#chi}^{0}",
     "TChizz": "#tilde{#chi}^{0}_{2}",
     "TChiSlep": "#tilde{#chi}^{0}_{2}",
     "TChiSlepSlep": "#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}",
     "TChiNuSlep": "#tilde{#chi}^{0}_{2}",
     "TSlepSlep":"#tilde{l}",
}

def describeTx (topo, short=True):
    """ describe a Tx name, e.g. T2tt -> "#tilde{t} -> t #tilde{#chi}^{0} """
    ret = topo + ": " + description (topo, plot = 'ROOT', kerning = False, short = short).replace("pp #rightarrow ", "")
    ret = ret[:ret.find(";")]
    return ret
    


def production(topo,plot='ROOT'):
  a=particles(topo)
  pair=str(a)+" "+str(a)
  if topo=="TGQ":
    pair=particles("T1")+" "+particles("T2")
  if topo=="TChiSlep":
    pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}"
  if topo=="TChiSlep":
    pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}"
  if topo=="TChiwz":
    pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}"
  if topo=="TChizz":
    pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{0}_{3}"
  if topo=="TChiNuSlep":
    pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}"
  if topo=="TChiSlepSlep":
    pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}"
#pair="#tilde{#chi}^{0}_{2}#tilde{#chi}^{0}_{2}"

  if plot == 'ROOT':
    return pair
  if plot == 'python':
    return pair.replace('#','\\')

def particles(topo,plot = 'ROOT'):
  """return the production mode for a given topology:
     latex code either compatible to ROOT or Python"""
  if dicparticle.has_key(topo):
    part = dicparticle[topo]
    if plot == 'ROOT':
      return part
    if plot == 'python':
      return part.replace('#','\\')
  else:
    return None
    
def description(topo,plot='ROOT',kerning=True,short=False):
  """ give a long description of the topology,
      with production, decay, and mass decoupling """
  if short:
    return "pp #rightarrow %s %s; %s" % ( production(topo,plot),  decays ( topo,plot,kerning, omitleft=True), massDecoupling ( topo,plot,kerning) )
  return "pp#rightarrow %s, %s; %s" % ( production(topo,plot), decays ( topo,plot,kerning, omitleft=False ), massDecoupling ( topo,plot,kerning) )
  
def particles(topo, plot='ROOT'):
    """return the production mode for a given topology:
         latex code either compatible to ROOT or Python"""
    if dicparticle.has_key(topo):
        part = dicparticle[topo]
        if plot == 'ROOT':
            # print "[SMSResults.py] debug",part
            return part
        if plot == 'python':
            return part.replace('#', '\\')
    else:
        return None

def particleName(topo):
    """return the production mode for a given topology:
         write out the name in plain letters, no latex """
    if topo[:2] == "TGQ": return "associate"
    if topo == "TChiSlep" or topo == "TChiNuSlep": return "chargino/neutralino"
    if topo == "TChiSlepSlep": return "chargino/neutralino"
    if topo == "TChiWZ": return "chargino/neutralino"
    if topo[:4] == "TChi": return "chargino/neutralino"
    if not dicparticle.has_key(topo):
        return "???"
    part = dicparticle[topo].replace("#tilde", "").replace("{", "").replace("}", "")
    if part == "g": part = "gluino"
    if part == "b": part = "sbottom"
    if part == "t": part = "stop"
    if part == "q": part = "squark"
    if part == "l": part = "slepton"
    return part

def massDecoupling_ (topo):
    if topo == "T2tt":
        return "m(#tilde{g},#tilde{q})>>m(#tilde{t})"
    if topo == "T2FVttcc":
        return "m(#tilde{g},#tilde{q})>>m(#tilde{t})"
    if topo == "T2bb":
        return "m(#tilde{g},#tilde{q})>>m(#tilde{b})"
    if topo == "TChiSlep":
        # return "m(#tilde{g}),m(#tilde{q})>>m(#tilde{#chi}^{0}_{2}),m(#tilde{#chi}^{#pm})"
        return "m(#tilde{g},m(#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
    if topo == "TChiSlepSlep":
# return "m(#tilde{g}),m(#tilde{q})>>m(#tilde{#chi}^{0}_{2})"
        return "m(#tilde{g},#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
    if topo == "TChiNuSlep":
        return "m(#tilde{g},#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
        # return "m(#tilde{g}),m(#tilde{q})>>m(#tilde{#chi}^{0}_{2}),m(#tilde{#chi}^{#pm})"
    if topo == "TChiwz":
        return "m(#tilde{g},#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
    T2 = topo[:2]
    if T2 == "T1" or T2 == "T3" or T2 == "T5":
        return "m(#tilde{q})>>m(#tilde{g})"
    if T2 == "T2" or T2 == "T4" or T2 == "T6":
        return "m(#tilde{g})>>m(#tilde{q})"
    return ""

def massDecoupling (topo, plot='ROOT', kerning=True):
    """ describe the assumed mass decoupling """
    md = massDecoupling_ (topo)
    if kerning:
        md = md.replace(">>", ">#kern[-.2]{>}")
    if plot != 'ROOT':
        md = '$' + md.replace('#', '\\') + '$'
    return md


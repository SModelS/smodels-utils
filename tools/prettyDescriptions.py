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

prettySMParticle = {

	'graviton':'#tilde{G}',         #graviton
	'photon': '#gamma',             #photon
	'gluon':'g',                    #gluon
	'w' : 'W',                  #W
	'z' : 'Z',                  #Z
	'higgs' : 'H',                  #higgs
	
	'quark': 'q',           #quark
	'up': 'u',           #up
	'down': 'd',           #down
	'charm': 'c',           #charm
	'strange': 's',           #strange
	'top': 't',           #top
	'bottom': 'b',           #bottom
	
	'lepton' : 'l',             #lepton
	'electron' : 'e',               #electron
	'muyon' : '#mu',            #myon
	'tauon' : '#tau',  #tauon
	
	'neutrino' : '#nu',                     #neutrino
	'elektron-neutrino' : '#nu_{e}',               #elektron-neutrino
	'myon-neutrino' : '#nu_{#mu}',            #myon-neutrino
	'tauon-neutrino' : '#nu_{#tau}',          #tauon-neutrino

}

prettySUSYParticle = {
    'lsp' : '#tilde{#chi}^{0}_{1}',  # lightesd SUSY particle
    'neutralino' : '#chi^{0}',      #neutralino
    'chargino' : '#chi',            #Chargino
    'gravitino':'G',              #gravitino
    'photino':'#tilde{#gamma}',   #photino
    'gluino': '#tilde{g}',        #gluino
    'wino' : '#tilde{W}',       #Wino
    'zino' : '#tilde{Z}',       #Zino
    'higgsino' : '#tilde{H}',       #higgsino
    
    'squark': '#tilde{q}',  #squark
    'sup': '#tilde{u}',  #sup
    'sdown': '#tilde{d}',  #sdown
    'scharm': '#tilde{c}',  #scharm
    'sstrange': '#tilde{s}',  #sstarnge
    'stop': '#tilde{t}',  #stop
    'sbottom': '#tilde{b}',  #sbottom
    
    'slepton' : '#tilde{l}',    #slepton
    'selectron' : '#tilde{e}',      #selectron
    'smyon' : '#tilde{#mu}',   #smyon
    'stauon' : '#tilde{#tau}', #stauon
    
    'sneutrino' : '#tilde{#nu}',            #sneutrino
    'elektron-sneutrino' : '#tilde{#nu}_{e}',      #elektron-sneutrino
    'myon-sneutrino' : '#tilde{#nu}_{#mu}',   #myon-sneutrino
    'tauon-sneutrino' : '#tilde{#nu}_{#tau}', #tauon-sneutrino

   
}

highstrings = {
    '^0' : '^{0}',
    '^pm' : '^{#pm}',
    '^p' : '^{+}',
    '^m' : '^{-}',
}

lowstrings = {
    '_1' : '_{1}',
    '_2' : '_{2}',
    '_3' : '_{3}',
    '_4' : '_{4}',
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

decay = { 'T1': 'gluino  --> quark antiquark  lsp ' , #tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{1}', 
	'T1bbbb': 'gluino  --> bottom antibottom  lsp ', #tilde{g} #rightarrow b#bar{b} #tilde{#chi}^{0}_{1}',
	'T1tttt': 'gluino  --> top antitop  lsp ', #tilde{g} #rightarrow t#bar{t} #tilde{#chi}^{0}_{1}',
	'T1gg':'gluino  --> quark antiquark (neutralino_2 --> photon lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow #gamma#tilde{#chi}^{0}_{1})',
	'T1lg':'gluino  --> quark antiquark (neutralino_2  --> photon lsp |chargino^pm  --> w lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow#gamma#tilde{#chi}^{0}_{1}|#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
	'T1lnu':'gluino  --> quark antiquark (chargino^pm --> lepton^pm neutrino  lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm} #rightarrow l^{#pm}#nu #tilde{#chi}^{0}_{1})',
	'T1lh':'gluino  --> quark antiquark  neutralino_2 neutralino_2  --> lepton^p lepton^m lsp ', #tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{2},#tilde{#chi}^{0}_{2} #rightarrow l^{+}l^{-}#tilde{#chi}^{0}_{1}',
	'T2':'squark  --> quark lsp ',#tilde{q} #rightarrow q #tilde{#chi}^{0}_{1}',
	'T2FVttcc': 'stop  --> charm lsp ',#tilde{t} #rightarrow c #tilde{#chi}^{0}_{1}',
    'T2llnunubb': 'stop  --> lepton neutrino bottom lsp ',#tilde{t} #rightarrow l #nu b #tilde{#chi}^{0}_{1}',
    'T2bb':'sbottom  --> bottom lsp ', #tilde{b} #rightarrow b #tilde{#chi}^{0}_{1}',
    'T2bw':'stop  --> bottom (chargino^pm_1 --> w lsp )',#tilde{t} #rightarrow b (#tilde{#chi}^{#pm}_{1} #rightarrow W #tilde{#chi}^{0}_{1})',
    'T2ttww': 'sbottom  --> top w lsp ',#tilde{b} #rightarrow tW #tilde{#chi}^{0}_{1}',
    'T2tt': 'stop  --> top lsp ', #tilde{t} #rightarrow t #tilde{#chi}^{0}_{1}',
    'T3w': 'gluino --> quark antiquark (chargino^pm_1 --> w lsp | lsp )' ,#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1} | #tilde{#chi}^{0}_{1})',
    'T3wb':'gluino  --> bottom antibottom (w )lsp ', #tilde{g} #rightarrow b#bar{b}(W)#tilde{#chi}^{0}_{1}',
    'T3lh':'gluino  --> quark antiquark (neutralino_2 --> lepton^p lepton^m lsp | lsp )',#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow l^{+}l^{-}#tilde{#chi}^{0}_{1})',
    'T3tauh':'gluino  --> quark antiquark (neutralino_2 --> tauon tauon lsp | lsp )', #tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{2}#rightarrow #tau #tau #tilde{#chi}^{0}_{1} |#tilde{#chi}^{0}_{1})',
    'T5WW':'gluino  --> quark antiquark (chargino^pm_1 --> w lsp )',#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
    'T5wg':'gluino  --> quark antiquark (neutralino_2 --> photon lsp | chargino^pm_1 --> w lsp )',#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow#gamma#tilde{#chi}^{0}_{1}|#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
    'T5WH':'gluino  --> quark antiquark (neutralino_2 --> higgs lsp | chargino^pm_1 --> w lsp )',#tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1} H#tilde{#chi}^{0}_{1} ',
    'T5gg':'gluino  --> quark antiquark (neutralino_2 --> photon lsp )',#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow #gamma#tilde{#chi}^{0}_{1})',
    'T5lnu':'gluino  --> quark antiquark (chargino^pm --> lepton^pm neutrino lsp )',#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm} #rightarrow l^{#pm}#nu #tilde{#chi}^{0}_{1})',
    'T5ZZ':'gluino  --> quark antiquark (neutralino_2 --> z lsp )',#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow Z #tilde{#chi}^{0}_{1})',
    'T5ZZInc':'neutralino_2 --> z lsp ',#tilde{#chi}^{0}_{2} #rightarrow Z #tilde{#chi}^{0}_{1}',
    'T5zzgmsb':'gluino --> quark antiquark (neutralino_2 --> z lsp )', #tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow Z #tilde{#chi}^{0}_{1})',
    'T5tttt':'gluino  --> top (stop --> top antitop lsp )',#tilde{g} #rightarrow t(#tilde{t} #rightarrow t#tilde{#chi}^{0}_{1})',
    'T6ttww': 'sbottom  --> top (chargino^pm_1 --> w lsp )',#tilde{b} #rightarrow tW #tilde{#chi}^{0}_{1}',
    'T6ttHH': 'stop  --> top higgs lsp ',#tilde{t} #rightarrow tH #tilde{#chi}^{0}_{1}',
    'T6ttzz': 'stop_2  --> stop_1 z --> top lsp ',#tilde{t}_{2} #rightarrow tilde{t}_{1}Z #rightarrow #tilde{#chi}^{0}_{1}t',
    'T6bbWW':'stop  --> bottom (chargino^p --> w lsp )',#tilde{t} #rightarrow b(#tilde{#chi}^{+} #rightarrow W#tilde{#chi}^{0}_{1})',
    'T6bbZZ':'sbottom  --> bottom z lsp ',#tilde{b} #rightarrow bZ #tilde{#chi}^{0}_{1}',
    'T7btW':'gluino  --> bottom top w lsp ',#tilde{g} #rightarrow btW#tilde{#chi}^{0}_{1}',
    'T7btbtWW':'gluino  --> bottom (sbottom --> top (chargino^pm --> w lsp ))',#tilde{g} #rightarrow b(#tilde{b} #rightarrow t(#tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1}))',
    'TChiwz':'chargino^pm neutralino_2  --> w z lsp lsp ',#tilde{#chi}^{#pm} #tilde{#chi}^{0}_{2} #rightarrow W Z #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1}',
    'TChizz':'neutralino_3 neutralino_2  --> z z lsp lsp ',#tilde{#chi}^{0}_{3} #tilde{#chi}^{0}_{2} #rightarrow Z Z #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1}',
    'TChiSlep':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow l l l #nu #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiNuSlep':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow l l l #nu #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiSlepSlep':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmHW':'neutralino_2 chargino^pm_1  --> w lsp higgs lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1} H#tilde{#chi}^{0}_{1} ',
    'TChiChipmSlepL':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmSlepSlep':'neutralino_2 chargino^pm_1  --> lepton lepton lepton neutrino lsp lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmSlepStau':'neutralino_2 chargino^pm_1  --> lepton lepton tauon neutrino lsp lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow ll#tau #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmStauStau':'neutralino_2 chargino^pm_1  --> tauon tauon tauon neutrino lsp lsp ',#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow #tau#tau#tau #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChipChimSlepSnu':'chargino^p chargino^m  --> lepton^p lepton^m neutrino neutrino lsp lsp ',#tilde{#chi}^{+}#tilde{#chi}^{-} #rightarrow l^{+}l^{-}#nu#nu#tilde{#chi}^{0}_{1}#tilde{#chi}^{0}_{1}',
    'TSlepSlep':'slepton  --> lepton lsp '#tilde{l} #rightarrow l #tilde{#chi}^{0}_{1}'
}

def latexParticle(decayString,key,value):
    decayString = decayString.replace('anti' + key + ' ','#bar{' + value + '}')
    decayString = decayString.replace(key + ' ',value)
    decayString = decayString.replace(key + '_',value + '_')
    decayString = decayString.replace(key + '^',value + '^')
    return decayString

def prettyDecay(topoName):
    if not topoName in decay: return None
    decayString = decay[topoName]
    for key, value in prettySUSYParticle.items():
        decayString = latexParticle(decayString,key,value)
    for key, value in prettySMParticle.items():
        decayString = latexParticle(decayString,key,value)
    for key, value in highstrings.items():
        decayString = decayString.replace(key,value)
    for key, value in lowstrings.items():
        decayString = decayString.replace(key,value)
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


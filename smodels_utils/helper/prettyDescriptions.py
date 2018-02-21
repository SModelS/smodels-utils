#!/usr/bin/env python

'''
.. module:: prettyDescriptions
   :synopsis: Module to provide some latex-coded strings needed for summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>


'''
import logging
from sympy import var
#For evaluating axes expressions in prettyAxes:
x,y,z = var('x y z')

# pretty name of particle:

prettySMParticle = {
	'graviton':'G',         #graviton
	'photon': '#gamma',             #photon
	'gluon':'g',                    #gluon
	'w' : 'W',                  #W
	'z' : 'Z',                  #Z
	'higgs' : 'H',                  #higgs
	
	'quark': 'q',           #quark
    'antiquark': '#bar{q}',
	'up': 'u',           #up
	'down': 'd',           #down
	'charm': 'c',           #charm
	'strange': 's',           #strange
	'top': 't',           #top
    'antitop': '#bar{t}',
	'bottom': 'b',           #bottom
    'antibottom': '#bar{b}',
	
	'lepton' : 'l',             #lepton
	'electron' : 'e',               #electron
	'muon' : '#mu',            #muon
	'tau' : '#tau',  #tau
	
	'neutrino' : '#nu',                     #neutrino
	'electron-neutrino' : '#nu_{e}',               #electron-neutrino
	'muon-neutrino' : '#nu_{#mu}',            #muon-neutrino
	'tau-neutrino' : '#nu_{#tau}',          #tau-neutrino
}

prettySUSYParticle = {
    'lsp' : '#tilde{#chi}^{0}_{1}',  # lightesd SUSY particle
    'neutralino' : '#tilde{#chi}^{0}',      #neutralino
    'chargino' : '#tilde{#chi}',            #Chargino
    'gravitino':'#tilde{G}',              #gravitino
    'gluino': '#tilde{g}',        #gluino
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
    'smuon' : '#tilde{#mu}',   #smuon
    'stau' : '#tilde{#tau}', #stau
    
    'sneutrino' : '#tilde{#nu}',            #sneutrino
    'electron-sneutrino' : '#tilde{#nu}_{e}',      #electron-sneutrino
    'muon-sneutrino' : '#tilde{#nu}_{#mu}',   #muon-sneutrino
    'tau-sneutrino' : '#tilde{#nu}_{#tau}', #tau-sneutrino
   
}

prettyParticle = prettySMParticle.copy()
prettyParticle.update(prettySUSYParticle)

highstrings = {
    '^0' : '^{0}',
    '^pm' : '^{#pm}',
    '^mp' : '^{#mp}',
    '^p' : '^{+}',
    '^m' : '^{-}',
    '^*' : '*',
}

lowstrings = {
    '_1' : '_{1}',
    '_2' : '_{2}',
    '_3' : '_{3}',
    '_4' : '_{4}',
}

# pretty name of decay:

decayDict = { 'T1': 'gluino  --> quark antiquark  lsp ' ,
    'T1bbbb': 'gluino  --> bottom antibottom  lsp ',
    'T1bbbt': 'gluino gluino  --> bottom antibottom bottom top lsp lsp',
    'T1bbqq': 'gluino gluino  --> bottom antibottom quark antiquark lsp lsp',
    'T1bbtt': 'gluino gluino  --> bottom antibottom top antitop lsp lsp',
    'T1btbt': 'gluino  --> bottom top  lsp ',
    'T1btqq': 'gluino gluino  --> bottom top quark antiquark lsp lsp',
    'T1bttt': 'gluino gluino  --> bottom top top antitop lsp lsp',
    'T1qqtt': 'gluino gluino  --> quark antiquark top antitop lsp lsp',
    'T1tttt': 'gluino  --> top antitop  lsp ',
    'T1ttttoff': 'gluino  --> top^* antitop^* lsp ',
    'T2':'squark  --> quark lsp ',
    'T2bb':'sbottom  --> bottom lsp ',
    'T2bbWW':'stop  --> bottom W lsp ',
    'T2bbWWoff':'stop  --> bottom W^* lsp ',
    'T2bbffff':'stop  --> bottom f f lsp ',
    'T2bt':'sbottom sbottom  --> bottom top lsp lsp',
    'T2cc':'stop  --> charm lsp ',
    'T2tt': 'stop  --> top lsp ', 
    'T2ttC': 'stop -->  b f fbar lsp',
    'T2bWC': 'stop -->  b chargino, chargino --> f fbar lsp',
    'T2ttoff': 'stop  --> top^* lsp ', 
    'T4bbWW':'stop --> bottom chargino^pm_1, chargino^pm_1 --> W lsp',
    'T4bbWWoff':'stop --> bottom chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T4bbffff':'stop --> bottom chargino^pm_1, chargino^pm_1 --> f f lsp',
    'T5':'gluino  --> quark squark, squark --> quark lsp',
    'T5gg':'gluino --> quark lsp',
    'T6gg':' squark --> quark lsp',
    'T5WW':'gluino  --> quark antiquark chargino^pm_1, chargino^pm_1 --> W lsp',
    'T5WWoff':'gluino  --> quark antiquark  chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T5ttbbWW':'gluino  --> top bottom chargino^pm_1, chargino^pm_1 --> W lsp',
    'T5ttbbWWoff':'gluino  --> top bottom chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T5ZZ':'gluino  --> quark antiquark neutralino_2, neutralino_2 --> Z lsp',
    'T5ZZG':'gluino  --> quark antiquark neutralino_1, neutralino_1 --> Z gravitino',
    'T5ZZoff':'gluino  --> quark antiquark neutralino_2, neutralino_2 --> Z^* lsp',
    'T5bbbb':'gluino  --> bottom sbottom, sbottom --> bottom lsp',
    'T5bbbt':'gluino gluino --> bottom sbottom bottom sbottom, sbottom --> bottom lsp, sbottom --> top lsp',
    'T5btbt':'gluino --> bottom sbottom, sbottom --> top lsp',
    'T5tbtb':'gluino --> top stop, stop --> bottom lsp',
    'T5tbtt':'gluino gluino --> top stop top stop, stop --> bottom lsp, stop --> top lsp',
    'T5tctc':'gluino --> top stop, stop --> charm lsp',
    'T5tqtq':'gluino --> top stop, stop --> quark lsp',
    'T5gg':'gluino --> quark lsp',
    'T5tctcoff':'gluino --> top^* stop, stop --> charm lsp',    
    'T5tttt':'gluino  --> antitop stop, stop --> top lsp',
    'T5ttcc':'gluino --> antitop stop, stop --> charm lsp',
    'T5ttttoff':'gluino  --> antitop^* stop, stop --> top^* lsp',
    'T5ttofftt':'gluino --> antitop^* stop, stop --> top lsp',
    'T6gg':' squark --> quark lsp',
    'T6WW': 'squark  --> quark chargino^pm_1, chargino^pm_1 --> W lsp',
    'T6WWoff': 'squark  --> quark chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T6ZZtt': 'stop_2  --> Z stop_1, stop_1 --> top lsp',
    'T6ZZofftt': 'stop_2  --> Z^* stop_1, stop_1 --> top lsp',
    'T6HHtt': 'stop_2  --> H stop_1, stop_1 --> top lsp',
    'T6bbWW':'stop  --> bottom chargino_1^pm, chargino_1^pm --> W lsp',
    'T6bbHH':'sbottom  --> bottom neutralino_2, neutralino_2 --> h lsp',
    'T6bbWWoff':'stop  --> bottom chargino_1^pm, chargino_1^pm --> W^* lsp',
    'T6ttWW':'sbottom  --> top chargino_1^pm, chargino_1^pm --> W lsp',
    'T6ttWWoff':'sbottom  --> top chargino_1^pm, chargino_1^pm --> W^* lsp',
    'T6ttoffWW':'sbottom  --> top^* chargino_1^pm, chargino_1^pm --> W lsp',
    'TChiChiSlepSlep':'neutralino_3 neutralino_2  --> lepton slepton lepton slepton, slepton --> lepton lsp',
    'TChiChipmSlepL':'neutralino_2 chargino^pm_1  --> lepton slepton ( neutrino sneutrino ) lepton sneutrino ( neutrino slepton ), slepton --> lepton lsp, sneutrino --> neutrino lsp',
    'TChiChipmSlepStau':'neutralino_2 chargino^pm_1  --> lepton slepton neutrino stau, slepton --> lepton lsp, stau --> tau lsp',
    'TChiChipmStauL':'neutralino_2 chargino^pm_1  --> tau stau ( neutrino sneutrino ) tau sneutrino ( neutrino stau ), stau --> tau lsp, sneutrino --> neutrino lsp',
    'TChiChipmStauStau':'neutralino_2 chargino^pm_1  --> tau stau neutrino stau, stau --> tau lsp',
    'TChiWH':'neutralino_2 chargino^pm_1 --> H W lsp lsp ',
    'TChiWW':'chargino^pm_1 --> W lsp lsp ',
    'TChiZZ':'neutralino_2 --> Z lsp lsp ',
    'TChiWWoff':'chargino^pm_1 --> W^* lsp lsp ',
    'TChiWZ':'neutralino_2 chargino^pm_1 --> Z W lsp lsp ',
    'TChiWZoff':'neutralino_2 chargino^pm_1 --> Z^* W^* lsp lsp ',
    'TChipChimSlepSnu':'chargino^pm_1 --> neutrino slepton ( lepton sneutrino ), slepton --> lepton lsp, sneutrino --> neutrino lsp ',
    'TChipChimStauSnu':'chargino^pm_1 --> neutrino stau ( tau sneutrino ), stau --> tau lsp, sneutrino --> neutrino lsp ',
    'TGQ':'gluino squark --> quark quark antiquark lsp lsp ',
    'TGQbbq':'gluino gluino --> bottom antibottom gluon lsp lsp ',
    'TGQbtq':'gluino gluino --> bottom top gluon lsp lsp ',
    'TGQqtt':'gluino gluino --> gluon top antitop lsp lsp ',
    'TScharm':'scharm  --> charm lsp ',
    'TSlepSlep':'slepton  --> lepton lsp ',
    'THSCPM1' : 'chargino^pm_1 chargino^pm_1 --> chargino^pm_1 chargino^pm_1', 'THSCPM3' : 'squark --> quark chargino_1', 'THSCPM5' : 'squark --> quark lsp, lsp --> tau stau_1', 
    'THSCPM7' : 'lsp chargino^pm_2 --> tau stau_1 chargino^pm_1, chargino^pm_1 --> nu stau_1',
    'THSCPM8' : 'squark --> quark quark stau_1', 'THSCPM2' : 'chargino^pm_1 lsp --> chargino^pm_1 lsp',
    'THSCPM4' : 'squark --> quark chargino_1 (quark lsp)',
    'THSCPM6' : 'squark squark --> quark quark lsp lsp, lsp --> tau tau_1',
    'THSCPM1b' : 'stau stau --> stau stau',
    'TRHadGM1' : 'gluino gluino --> gluino gluino',
    'TRHadQM1' : 'stop stop --> stop stop'
}

#Name of mother particles

motherDict = {"T1" :  "gluino", 
    "T1bbbb" :  "gluino", 
    "T1bbbt" :  "gluino", 
    "T1bbqq" :  "gluino", 
    "T1bbtt" :  "gluino", 
    "T1btbt" :  "gluino", 
    "T1btqq" :  "gluino", 
    "T1bttt" :  "gluino", 
    "T1qqtt" :  "gluino", 
    "T1tttt" :  "gluino", 
    "T1ttttoff" :  "gluino", 
    "T2" :  "squark", 
    "T2bb" :  "sbottom", 
    "T2bbWW" :  "stop", 
    "T2bbffff" :  "stop", 
    "T2bbWWoff" :  "stop", 
    "T2bt" :  "sbottom", 
    "T2cc" :  "stop", 
    "T2tt" :  "stop", 
    "T2ttC": "stop",
    "T2bWC": "stop",
    "T2ttoff" :  "stop", 
    "T2bbWWoff" :  "stop", 
    "T4bbffff" :  "stop", 
    "T4bbWW" :  "stop", 
    "T4bbWWoff" :  "stop", 
    "T5WW" :  "gluino", 
    "T5WWoff" :  "gluino", 
    "T5ttbbWW" :  "gluino", 
    "T5ttbbWWoff" :  "gluino", 
    "T5ZZ" :  "gluino", 
    "T5ZZG" :  "gluino", 
    "T5" :  "gluino", 
    "T5tctc" :  "gluino", 
    "T5gg": "gluino",
    "T6gg":"squark",
    "T5ZZoff" :  "gluino", 
    "T5bbbb" :  "gluino", 
    "T5bbbt" :  "gluino", 
    "T5btbt" :  "gluino", 
    "T5tbtb" :  "gluino", 
    "T5tbtt" :  "gluino", 
    "T5tctc" :  "gluino",
    "T5tqtq" :  "gluino",
    "T5gg": "gluino",
    "T5tctcoff" :  "gluino",      
    "T5ttcc": "gluino",
    "T5tttt" :  "gluino", 
    "T5ttttoff" :  "gluino", 
    "T5ttofftt" : "gluino",
    "T6WW" :  "squark", 
    "T6WWoff" :  "squark", 
    "T6ZZtt" :  "stop_2", 
    "T6ZZofftt" :  "stop_2", 
    "T6HHtt" :  "stop_2", 
    "T6bbWW" :  "stop",
    "T6bbHH" :  "sbottom",      
    "T6bbWWoff" :  "stop", 
    "T6ttWW" :  "sbottom", 
    "T6ttWWoff" :  "sbottom", 
    "T6ttoffWW" :  "sbottom", 
    "TChiChiSlepSlep" :  "neutralino_3 neutralino_2", 
    "TChiChipmSlepL" :  "neutralino_2 chargino^pm_1", 
    "TChiChipmSlepStau" :   "neutralino_2 chargino^pm_1", 
    "TChiChipmStauL" :  "neutralino_2 chargino^pm_1", 
    "TChiChipmStauStau" :  "neutralino_2 chargino^pm_1", 
    "TChiWH" :  "neutralino_2 chargino^pm_1", 
    "TChiWW" :  "chargino^+_1 chargino^-_1",
    "TChiWWoff" :  "chargino^+_1 chargino^-_1", 
    "TChiWZ" :  "neutralino_2 chargino^pm_1", 
    "TChiZZ" :  "neutralino_2",
    "TChiWZoff" :  "neutralino_2 chargino^pm_1", 
    "TChipChimSlepSnu" :   "chargino^pm_1 chargino^pm_1", 
    "TChipChimStauSnu" :  "chargino^pm_1 chargino^pm_1", 
    "TGQ" :  "gluino squark", 
    "TGQbbq" :  "gluino", 
    "TGQbtq" :  "gluino", 
    "TGQqtt" :  "gluino", 
    "TScharm" :  "scharm",
    "TSlepSlep" : "slepton",
    "THSCPM1" : "chargino^pm_1",
    "THSCPM1b" : "stau",
    "THSCPM3" : "squark",
    "THSCPM5" : "squark",
    "THSCPM7" : "lsp chargino^pm_2",
    "THSCPM8" : "squark",
    "THSCPM2" : "lsp chargino^pm_1",
    "THSCPM4" : "squark",
    "THSCPM6" : "squark",
    'TRHadGM1' : 'gluino',
    'TRHadQM1' : 'stop'    
}


def latexfy(instr):
    """
    Tries to convert the string to its latex form,
    using ROOT conventions
    
    :param instr: Input string
    
    :return: String converted to its latex form (if possible)
    """
    
    outstr = ' '+instr[:]
    for key,rep in highstrings.items():
        if key in outstr:
            outstr = outstr.replace(key,rep)
    for key,rep in lowstrings.items():
        if key in outstr:
            outstr = outstr.replace(key,rep)
    #Make sure that the largest replacement happen first 
    #(e.g. stau -> #tilde{#tau} happens before tau -> #tilde{#tau}
    for key,rep in sorted(prettyParticle.items(),  
                          key=lambda pair: len(pair[0]), reverse=True):
        if ' '+key in outstr:
            outstr = outstr.replace(' '+key,' '+rep)
    
    outstr = outstr.replace('-->','#rightarrow')


    return outstr.lstrip().rstrip()

def getMothers(txname):
    """
    Returns the SUSY mother particle(s) for the txname.
    
    :param txname: txname string (e.g. 'T1')
    
    :return: list of mother particles in standard format (e.g. ['gluino', 'gluino'])
    """
    
    mothers = motherDict[txname].lstrip().rstrip().split()
    if len(mothers) == 1:
        mothers = mothers*2
    
    return mothers

def getIntermediates(txname):
    """
    Returns the SUSY intermediate particle(s) for the txname.
    
    :param txname: txname string (e.g. 'T1')
    
    :return: list of intermediate particles in standard format (e.g. ['stop', 'chargino^pm_1'])
    """
    
    #Get the decays
    decays = decayDict[txname].split(',')
    #Find the subsequent decays:
    inter = [d.split('-->')[0].strip() for d in decays[1:]]
    first_decay = decays[0].split('-->')[1]
    #Check if the intermediate particles appear in the first decay
    #(sanity check)
    for particle in inter:
        if not particle in first_decay:
            logging.error('Unknown decay format: %s' %str(decays))

    return inter

def getDaughters(txname):
    """
    Returns the SUSY daughter particle(s) for the txname.
    
    :param txname: txname string (e.g. 'T1')
    
    :return: list of daughter particles in standard format (e.g. ['lsp', 'chargino^pm_1'])
    """
    
    #Get the decays
    decays = decayDict[txname].split(',')
    #Find the subsequent decays:
    moms = [d.split('-->')[0].strip() for d in decays]
    daughters = set()
    for d in decays:
        for ptc in  d.split('-->')[1].split():
            if not ptc in prettySUSYParticle:
                continue
            if ptc in moms:
                continue       
            daughters.add(ptc)

    return list(daughters)


def prettyProduction(txname,latex=True):
    """
    Converts the txname string to the corresponding SUSY production process
    in latex form (using ROOT conventions)
    :param: txname (string) (e.g. 'T1')
    :param latex: If True it will return the latex version, otherwise
                 it will return a more human readable string
    
    :return: string or latex string (e.g. p p #rightarrow #tilde{g} #tilde{g})
    """    
    if not txname in motherDict:
        logging.error("Txname %s not found in motherDict" %txname)
        return None
    
    prodString = motherDict[txname].lstrip().rstrip().split()
    #Check if a single mother was given. If so, duplicate it
    if len(prodString) == 1:
        prodString = prodString[0]+" "+prodString[0]
    elif len(prodString) == 2:
        prodString = prodString[0]+" "+prodString[1]
    else:
        logging.error("More than two mothers given: %s" %motherDict[txname])
        return None
    
    prodString = "pp --> "+prodString
    if latex:
        prodString = latexfy(prodString)
    return prodString.lstrip().rstrip()

def prettyDecay(txname,latex=True):
    """
    Converts the txname string to the corresponding SUSY decay process
    in latex form (using ROOT conventions)
    :param: txname (string) (e.g. 'T1')
    :param latex: If True it will return the latex version, otherwise
                 it will return a more human readable string
    
    
    :return: string or latex string (e.g. #tilde{g} #rightarrow q q #tilde{#chi}_{1}^{0})
    """
    
    if not txname in decayDict:
        logging.error("Txname %s not found in decayDict" %txname)
        return None
    decayString = decayDict[txname]
    if latex:
        decayString = latexfy(decayString)
    return decayString.lstrip().rstrip()

    
def prettyTxname(txname,latex=True):
    """
    Converts the txname string to the corresponding SUSY desctiption
    in latex form (using ROOT conventions)
    :param: txname (string) (e.g. 'T1')
    :param latex: If True it will return the latex version, otherwise
                 it will return a more human readable string
    
    
    :return: string or latex string 
             (e.g. pp #rightarrow #tilde{g} #tilde{g}, 
             #tilde{g} #rightarrow q q #tilde{#chi}_{1}^{0})
    """

    prodString = prettyProduction(txname,latex)
    decayString = prettyDecay(txname,latex)
    
    if prodString and decayString:    
        return prodString + ", " + decayString
    else:
        return None

def prettyAxes(txname,axes):
    """
    Converts the axes string to the axes labels (plus additional constraints)
    in latex form (using ROOT conventions)
    :param txname: txname string  (e.g. 'T1')
    :param axes: axes string (e.g. '2*Eq(mother,x)_Eq(inter0,0.05*x+0.95*y)_Eq(lsp,y)')
    
    :return: dictionary with the latex labels 
             (e.g. {'x' : m_{#tilde{g}}, 'y' : m_{#tilde{#chi}_{1}^{0}}
             'constraints' : [m_{#tilde{l}} = 0.05*m_{#tilde{g}} + 0.95*m_{#tilde{#chi}_{1}^{0}}]})
    """
    
    #Build axes object (depending on symmetric or asymmetric branches:
    axes = eval(axes)
    if txname == 'TGQ':
        return ['m_{#tilde{g}} = x, m_{#tilde{q}} = 0.96*x',
                    'm_{#tilde{#chi}_{1}^{0}} = y']
    elif txname == 'TChiChiSlepSlep':
        return ['m_{#tilde{#chi}_{3}^{0} = x+80.0, m_{#tilde{#chi}_{2}^{0} = x+75.0',
                    'm_{#tilde{#l}} = x-y+80.0',
                    'm_{#tilde{#chi}_{1}^{0}} = x']
    elif axes[0] != axes[1]:
        logging.error('Asymmetric branches are not yet automatized.')
        return None
        
    ax = axes[0]
    if len(ax) > 3:
        logging.error("Nice axes with more than one \
        intermetiate particle is not available.")
        return None

    #Get mother particles:
    motherList = list(set(getMothers(txname)))
    #Convert to latex for mass:
    motherList = ['m_{'+latexfy(mother)+'}' for mother in motherList]
    motherStr = str(motherList).replace(']','').replace('[','')
    #Get intermediate particles:
    interList = list(set(getIntermediates(txname)))
    #Convert to latex for mass:
    interList = ['m_{'+latexfy(inter)+'}' for inter in interList]
    interStr = str(interList).replace(']','').replace('[','')
    #Daugther particles are always trivial:
    daughterList = list(set(getDaughters(txname)))
    #Convert to latex for mass:
    daughterList = ['m_{'+latexfy(daughter)+'}' for daughter in daughterList]
    daughterStr = str(daughterList).replace(']','').replace('[','')

    #Define mass strings for each axes format:
    if len(ax) == 1:
        massStrings = [motherStr]
    elif len(ax) == 2:
        massStrings = [motherStr,daughterStr]
    else:
        massStrings = [motherStr,interStr,daughterStr]

    niceAxes = []    
    for i,eq in enumerate(ax):
        axStr = massStrings[i].strip()+'='+str(eq)
        niceAxes.append(axStr.replace("'",""))
    
    return niceAxes
        

#!/usr/bin/env python

'''
.. module:: prettyDescriptions
   :synopsis: Module to provide some latex-coded strings needed for summaryplots.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>


'''
import logging
from sympy import var
from math import floor, log10
from smodels.tools.physicsUnits import TeV
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
 'nu' : '#nu',            #neutrino
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
    'chargino^pm_1' : '#tilde{#chi}^{#pm}_{0}',            #Chargino
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
    'stau_1' : '#tilde{#tau}_{1}', #stau
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
    'T1ttofftt': 'gluino  --> top^* antitop^* lsp ',
    'T2':'squark  --> quark lsp ',
    'T2onesquark':'squark  --> q lsp ',
    'T2bb':'sbottom  --> bottom lsp ',
    'T2bbWW':'stop  --> bottom W lsp ',
    'T2bbWWoff':'stop  --> bottom W^* lsp ',
    'T2bbWWoffMu':'stop  --> bottom W^* lsp, W^* --> mu neutrino',
    'T2bbWWoffSemiLep':'stop  --> bottom W^* lsp, W^* --> l neutrino',
    'T2bbffff':'stop  --> bottom f f lsp',
    'T2bt':'sbottom sbottom  --> bottom top lsp lsp',
    'T2cc':'stop  --> charm lsp ',
    'T2tt': 'stop  --> top lsp ',
    'T2ttC': 'stop -->  b f fbar lsp',
    'T2bWC': 'stop -->  b chargino, chargino --> f fbar lsp',
    'T2ttoff': 'stop  --> top^* lsp ',
    'T2bbll': 'stop  --> top^* lsp ',
    'T3GQ' : 'gluino --> squark quark, squark --> quark LSP',
    'T3GQon' : 'gluino --> squark quark, squark --> quark LSP',
    'T4bbWW':'stop --> bottom chargino^pm_1, chargino^pm_1 --> W lsp',
    'T4bbWWoff':'stop --> bottom chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T4bbffff':'stop --> bottom chargino^pm_1, chargino^pm_1 --> f f lsp',
    'T4bnutaubnutau': 'stop --> b nu stau, stau --> tau lsp',
    'T5Chi': 'gluino --> quark antiquark neutralino_2, neutralino_2 --> photon neutralino_1',
    'T5':'gluino  --> quark squark, squark --> quark lsp',
    'T5GQ' : 'gluino --> quark quark, squark --> quark gluino',
    'T5Disp':'gluino  --> quark quark lsp',
    'T2Disp':'gluino  --> g lsp',
    'T5gg':'gluino --> quark lsp',
    'T6gg':' squark --> quark lsp',
    'T5WW':'gluino  --> quark antiquark chargino^pm_1, chargino^pm_1 --> W lsp',
    'T5WWoff':'gluino  --> quark antiquark  chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T5ttbbWW':'gluino  --> top bottom chargino^pm_1, chargino^pm_1 --> W lsp',
    'T5ttbbWWoff':'gluino  --> top bottom chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T5WZ':'gluino  --> quark quark antiquark antiquark chargino^pm_1 neutralino_2, chargino^pm_1 --> W lsp, neutralino_2 --> Z lsp',
    'T5WZh':'gluino  --> quark quark antiquark antiquark chargino^pm_1 neutralino_2, chargino^pm_1 --> W lsp, neutralino_2 --> Z|h lsp',
    'T5ZZ':'gluino  --> quark antiquark neutralino_2, neutralino_2 --> Z lsp',
    'T5HH':'gluino  --> quark antiquark neutralino_2, neutralino_2 --> H lsp',
    'T5HZ':'gluino  --> quark antiquark neutralino_2, neutralino_2 --> H|Z lsp',
    'T5ZZG':'gluino  --> quark antiquark neutralino_1, neutralino_1 --> Z gravitino',
    'T5ZZoff':'gluino  --> quark antiquark neutralino_2, neutralino_2 --> Z^* lsp',
    'T5bbbb':'gluino  --> bottom sbottom, sbottom --> bottom lsp',
    'T5bbbbZGamma':'gluino  --> bottom sbottom, sbottom --> bottom neutralino_2 --> Z/photon neutralino_1',
    'T5bbbbZg':'gluino  --> bottom sbottom, sbottom --> bottom neutralino_2 --> Z/photon neutralino_1',
    'T5ttttZGamma':'gluino  --> bottom sbottom, sbottom --> bottom neutralino_2 --> Z/photon neutralino_1',
    'T5ttttZg':'gluino  --> bottom sbottom, sbottom --> bottom neutralino_2 --> Z/photon neutralino_1',
    'T6ttZGamma':'stop  --> top neutralino_2 --> --> Z/photon neutralino_1',
    'T6ttZg':'stop  --> top neutralino_2 --> --> Z/photon neutralino_1',
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
    'T5ZGamma': 'gluino --> quark antiquark neutralino_2, neutralino_2 --> Z/photon neutralino_1',
    'T5HGamma': 'gluino --> quark antiquark neutralino_2, neutralino_2 --> H neutralino_1',
    'T5Zg': 'gluino --> quark antiquark neutralino_2, neutralino_2 --> Z/photon neutralino_1',
    'T5Hg': 'gluino --> quark antiquark neutralino_2, neutralino_2 --> H neutralino_1',
  'T6Chi': 'squark --> quark neutralino_2, neutralino_2 --> photon neutralino_1',
    'T6gg':' squark --> quark lsp',
    'T6WW': 'squark --> quark chargino^pm_1, chargino^pm_1 --> W lsp',
    'T6WWleft': 'squark_{L} --> quark chargino^pm_1, chargino^pm_1 --> W lsp',
  'T6WZ': 'squark  --> quark antiquark chargino^pm_1 neutralino_2, chargino^pm_1 --> W lsp, neutralino_2 --> Z lsp',
  'T6WZh': 'squark  --> quark antiquark chargino^pm_1 neutralino_2, chargino^pm_1 --> W lsp, neutralino_2 --> Z|h lsp',
    'T6ZZ': 'squark  --> quark neutralino_2, neutralino_2 --> Z lsp',
    'T6WWoff': 'squark  --> quark chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T6WWoffleft': 'squark_{L}  --> quark chargino^pm_1, chargino^pm_1 --> W^* lsp',
    'T6ZZtt': 'stop_2  --> Z stop_1, stop_1 --> top lsp',
    'T6ZZofftt': 'stop_2  --> Z^* stop_1, stop_1 --> top lsp',
    'T6HHtt': 'stop_2  --> H stop_1, stop_1 --> top lsp',
    'T6bbWW':'stop  --> bottom chargino_1^pm, chargino_1^pm --> W lsp',
    'T6bbHH':'sbottom  --> bottom neutralino_2, neutralino_2 --> h lsp',
    'T6bbHHoff':'sbottom  --> bottom neutralino_2, neutralino_2 --> h^* lsp',
    'T6bbWWoff':'stop  --> bottom chargino_1^pm, chargino_1^pm --> W^* lsp',
    'T6bbWWoffSemiLep':'stop  --> bottom chargino_1^pm, chargino_1^pm --> W^* lsp; W^* --> l neutrino',
    'T6ttWW':'sbottom  --> top chargino_1^pm, chargino_1^pm --> W lsp',
    'T6ttWWoff':'sbottom  --> top chargino_1^pm, chargino_1^pm --> W^* lsp',
    'T6ttoffWW':'sbottom  --> top^* chargino_1^pm, chargino_1^pm --> W lsp',
    'T6ZZtt': 'stop_2 --> Z stop, stop --> t lsp',
    'T6ZZofftt': 'stop_2 --> Z^* stop, stop --> t lsp',
    'T6ZZttoff': 'stop_2 --> Z stop, stop --> t^* lsp',
    'T6ttZZ': 'stop --> t neutralino_2 , neutralino_2 --> Z lsp',
    'T6ttoffZZ': 'stop --> t^* neutralino_2 , neutralino_2 --> Z lsp',
    'T6ttZZoff': 'stop --> t neutralino_2 , neutralino_2 --> Z^* lsp',
    'T6ttWW':'sbottom  --> top chargino_1^pm, chargino_1^pm --> W lsp',
    'T6ttWWoff':'sbottom  --> top chargino_1^pm, chargino_1^pm --> W^* lsp',
    'T6ttoffWW':'sbottom  --> top^* chargino_1^pm, chargino_1^pm --> W lsp',
    'TChipChimGamma': 'chargino^pm_2 chargino^mp_2/neutralino_3 --> W neutralino_2 W/Z/h neutralino_2, neutralino_2 --> photon neutralino_1',
    'TChipChimg': 'chargino^pm_2 chargino^mp_2/neutralino_3 --> W neutralino_2 W/Z/h neutralino_2, neutralino_2 --> photon neutralino_1',
    'TChipChimgg': 'chargino^pm_2 chargino^mp_2/neutralino_3 --> W neutralino_2 W/Z/h neutralino_2, neutralino_2 --> photon neutralino_1',
    'TChiChiSlepSlep':'neutralino_3 neutralino_2  --> lepton slepton lepton slepton, slepton --> lepton lsp',
    'TChiChipmSlepL':'neutralino_2 chargino^pm_1  --> lepton slepton ( neutrino sneutrino ) lepton sneutrino ( neutrino slepton ), slepton --> lepton lsp, sneutrino --> neutrino lsp',
    'TChiChipmSlepSlep':'neutralino_2 chargino^pm_1  --> lepton slepton ( neutrino sneutrino ) lepton sneutrino ( neutrino slepton ), slepton --> lepton lsp, sneutrino --> neutrino lsp',
    'TChiChipmSlepLNoTau':'neutralino_2 chargino^pm_1  --> lepton slepton ( neutrino sneutrino ) lepton sneutrino ( neutrino slepton ), slepton --> lepton lsp, sneutrino --> neutrino lsp',
    'TChiChipmSlepStau':'neutralino_2 chargino^pm_1  --> lepton slepton neutrino stau, slepton --> lepton lsp, stau --> tau lsp',
    'TChiChipmStauL':'neutralino_2 chargino^pm_1  --> tau stau ( neutrino sneutrino ) tau sneutrino ( neutrino stau ), stau --> tau lsp, sneutrino --> neutrino lsp',
    'TChiChipmStauStau':'neutralino_2 chargino^pm_1  --> tau stau neutrino stau, stau --> tau lsp',
    'TChiWH':'neutralino_2 chargino^pm_1 --> H W lsp lsp ',
    'TChiWW':'chargino^pm_1 --> W lsp lsp ',
      'TChiH': 'neutralino_1 --> Z/h gravitino',
    'TChiZZ':'neutralino_2 --> Z lsp lsp ',
    'TChiWWoff':'chargino^pm_1 --> W^* lsp lsp ',
    'TChiWZ':'neutralino_2 chargino^pm_1 --> Z W lsp lsp ',
    'TChiWZoff':'neutralino_2 chargino^pm_1 --> Z^* W^* lsp lsp ',
    'TChiWZoffqq':'neutralino_2 chargino^pm_1 --> Z^* W^* lsp lsp ',
    'TChipChimSlepSnu':'chargino^pm_1 --> neutrino slepton ( lepton sneutrino ), slepton --> lepton lsp, sneutrino --> neutrino lsp ',
    'TChipChimStauSnu':'chargino^pm_1 --> neutrino stau ( tau sneutrino ), stau --> tau lsp, sneutrino --> neutrino lsp ',
    'TGQ':'gluino squark --> quark quark antiquark lsp lsp ',
    'TGQ12':'T1+T2+TGQ',
    'TGN':'gluino lsp --> quark quark lsp lsp',
    'TGQbbq':'gluino gluino --> bottom antibottom gluon lsp lsp ',
    'TGQbtq':'gluino gluino --> bottom top gluon lsp lsp ',
    'TGQqtt':'gluino gluino --> gluon top antitop lsp lsp ',
    'TScharm':'scharm  --> charm lsp ',
    'TSlepSlep':'slepton  --> lepton lsp ',
    'TSelSel':'selectron --> electron lsp ',
    'TSmuSmu':'smuon --> muon lsp ',
    'TStauStau':'stau  --> tau lsp ',
    'THSCPM1' : 'chargino^pm_1 chargino^pm_1 --> chargino^pm_1 chargino^pm_1',
    'THSCPM1b' : 'stau stau --> stau stau',
    'THSCPM1Disp' : 'chargino^pm_1 chargino^pm_1 --> chargino^pm_1 chargino^pm_1',
    'THSCPM2' : 'chargino^pm_1 lsp --> chargino^pm_1 lsp',
    'THSCPM2b' : 'stau lsp --> stau lsp',
    'THSCPM3' : 'squark --> quark chargino^pm_1',
    'THSCPM4' : 'squark --> quark chargino^pm_1, squark --> quark lsp',
    'THSCPM5' : 'squark --> quark lsp, lsp --> tau stau',
    'THSCPM6' : 'squark squark --> quark quark lsp lsp, lsp --> tau stau_1',
    'THSCPM7' : 'squark --> quark chargino_1 | quark neutralino_1, neutralino_1 --> W chargino_1',
    'THSCPM8' : 'squark --> quark quark stau_1',
    'THSCPM9' : 'squark --> quark quark stau_1, squark --> quark quark lsp',
    'TRHadGM1' : 'gluino gluino --> gluino gluino',
    'TRHadQM1' : 'squark squark --> squark squark',
    'TRHadUM1' : 'stop stop --> stop stop',
    'TRHadDM1' : 'sbottom sbottom --> sbottom sbottom',
    "T5Gamma" :    "gluino --> neutralino_1 quark antiquark, neutralino_1 --> gravitino y",
    "T5ZGamma" : "gluino --> neutralino_1 quark antiquark, neutralino_1 --> gravitino Z/y",
    "T5HGamma" : "gluino --> neutralino_1 quark antiquark, neutralino_1 --> gravitino H/y",
    "T6Gamma" :    "squark --> quark neutralino_1, neutralino_1 --> gravitino",
    "TChipChimGamma": "chargino^pm_1 chargino^mp_1/neutralino_2 --> W neutralino_1 W/Z neutralino_1, neutralino_1 --> gravitino y",
    "T5g" :    "gluino --> neutralino_1 quark antiquark, neutralino_1 --> gravitino y",
    "T5Zg" : "gluino --> neutralino_1 quark antiquark, neutralino_1 --> gravitino Z/y",
    "T5Hg" : "gluino --> neutralino_1 quark antiquark, neutralino_1 --> gravitino H/y",
    "T6g" :    "squark --> quark neutralino_1, neutralino_1 --> gravitino",
    "TChipChimg": "chargino^pm_1 chargino^mp_1/neutralino_2 --> W neutralino_1 W/Z neutralino_1, neutralino_1 --> gravitino y",
    'TSlepSlepAll':'slepton  --> lepton lsp ',
    'TChiChipmSlep':'neutralino_2 chargino^pm_1  --> lepton slepton ( neutrino sneutrino ) lepton sneutrino ( neutrino slepton ), slepton --> lepton lsp, sneutrino --> neutrino lsp',
    'TChipChimSlepSlepAll': 'chargino^pm_1 chargino^pm_1 --> lepton slepton lepton slepton, slepton --> lepton lsp',
    'TChipChimSlepSlep': 'chargino^pm_1 chargino^pm_1 --> lepton slepton lepton slepton, slepton --> lepton lsp'
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
    "T1ttofftt" :  "gluino",
    "T2" :  "squark",
    "T2onesquark" :  "sup_{L}, sdown_{L}",
    "T2bb" :  "sbottom",
    "T2bbWW" :  "stop",
    "T2bbffff" :  "stop",
    "T2bbWWoff" :  "stop",
    "T2bbWWoffMu" :  "stop",
    "T2bbWWoffSemiLep" :  "stop",
    "T2bt" :  "sbottom",
    "T2cc" :  "stop",
    "T2tt" :  "stop",
    "T2ttC": "stop",
    "T2bWC": "stop",
    "T2ttoff" :  "stop",
    "T2bbll" :  "stop",
    "T4bbffff" :  "stop",
    "T4bbWW" :  "stop",
    "T4bbWWoff" :  "stop",
    'T4bnutaubnutau': 'stop',
    "T5WW" :  "gluino",
    "T5Disp" :  "gluino",
    "T2Disp" :  "gluino",
    "T5WWoff" :  "gluino",
    "T5ttbbWW" :  "gluino",
    "T5ttbbWWoff" :  "gluino",
    "T5ZZ" :  "gluino",
    "T5HH" :  "gluino",
    "T5HZ" :  "gluino",
    "T5ZZG" :  "gluino",
    "T5" :  "gluino",
    "T5tctc" :  "gluino",
    "T5gg": "gluino",
    "T6gg":"squark",
  "T5Chi": "gluino",
    "T5ZZoff" :  "gluino",
    "T5bbbb" :  "gluino",
    "T5bbbbZGamma" :  "gluino",
    "T5ttttZGamma" :  "gluino",
    "T5bbbbZg" :  "gluino",
    "T5ttttZg" :  "gluino",
    "T6ttZGamma" :  "stop",
    "T6ttZg" :  "stop",
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
    "T5WZ" :  "gluino",
    "T5WZh" :  "gluino",
    "T5ZGamma" :  "gluino",
    "T5HGamma" :  "gluino",
    "T5Zg" :  "gluino",
    "T5Hg" :  "gluino",
    "T6Chi" :  "squark",
    "T6WW" :  "squark",
    "T6WWleft" :  "squark_{L}",
    "T6WZ" :  "squark",
    "T6WZh" :  "squark",
    "T6ZZ" :  "squark",
    "T6WWoff" :  "squark",
    "T6WWoffleft" :  "squark_{L}",
    "T6ZZtt" :  "stop_2",
    "T6ZZofftt" :  "stop_2",
    "T6HHtt" :  "stop_2",
    "T6bbWW" :  "stop",
    "T6bbHH" :  "sbottom",
    "T6bbHHoff" :  "sbottom",
    "T6bbWWoff" :  "stop",
    "T6bbWWoffSemiLep" :  "stop",
    "T6ttWW" :  "sbottom",
    "T6ttWWoff" :  "sbottom",
    "T6ttoffWW" :  "sbottom",
    "T6ttZZ": 'stop',
    "T6ttoffZZ": 'stop',
    "T6ttZZoff": 'stop',
    "T6ttWW":'sbottom',
    "T6ttWWoff":'sbottom',
    "T6ttoffWW":'sbottom',
    "T6WWtt":'sbottom',
    "T6WWofftt":'sbottom',
    "T6WWttoff":'sbottom',
    "T6ZZtt": 'stop_2',
    "T6ZZofftt": 'stop_2',
    "T6ZZttoff": 'stop_2',
    "TChipChimGamma" :  "chargino^pm_2 chargino^mp_2/neutralino_3",
    "TChipChimg" :  "chargino^pm_2 chargino^mp_2/neutralino_3",
    "TChipChimgg" :  "chargino^pm_2 chargino^mp_2/neutralino_3",
    "TChiChiSlepSlep" :  "neutralino_3 neutralino_2",
    "TChiChipmSlepL" :  "neutralino_2 chargino^pm_1",
    "TChiChipmSlepSlep" :  "neutralino_2 chargino^pm_1",
    "TChiChipmSlepLNoTau" :  "neutralino_2 chargino^pm_1",
    "TChiChipmSlepStau" :   "neutralino_2 chargino^pm_1",
    "TChiChipmStauL" :  "neutralino_2 chargino^pm_1",
    "TChiChipmStauStau" :  "neutralino_2 chargino^pm_1",
    "TChiWH" :  "neutralino_2 chargino^pm_1",
    "TChiWW" :  "chargino^pm_1 chargino^mp_1",
    "TChiWWoff" :  "chargino^+_1 chargino^-_1",
    "TChiWZ" :  "neutralino_2 chargino^pm_1",
    "TChiH" :  "neutralino_1",
    "TChiZZ" :  "neutralino_2",
    "TChiWZoff" :  "neutralino_2 chargino^pm_1",
    "TChiWZoffqq" :  "neutralino_2 chargino^pm_1",
    "TChipChimSlepSnu" :   "chargino^pm_1 chargino^pm_1",
    "TChipChimStauSnu" :  "chargino^pm_1 chargino^pm_1",
    "T3GQ": "gluino squark",
    "T3GQon": "gluino squark",
    "T5GQ": "gluino squark",
    "TGQ" :  "gluino squark",
    "TGQ12" :  "gluino squark",
    "TGQbbq" :  "gluino",
    "TGQbtq" :  "gluino",
    "TGQqtt" :  "gluino",
    "TGN":'gluino lsp',
    "TScharm" :  "scharm",
    "TSlepSlep" : "slepton",
    "TSelSel" : "selectron",
    "TSmuSmu" : "smuon",
    "TStauStau" : "stau",
    "THSCPM1" : "chargino^pm_1",
    "THSCPM1Disp" : "chargino^pm_1",
    "THSCPM1b" : "stau",
    "THSCPM2" : "lsp chargino^pm_1",
    "THSCPM2b" : "lsp stau",
    "THSCPM3" : "squark",
    "THSCPM4" : "squark",
    "THSCPM5" : "squark",
    "THSCPM6" : "squark",
    "THSCPM7" : "squark",
    "THSCPM8" : "squark",
    "THSCPM9" : "squark",
    'TRHadGM1' : 'gluino',
    'TRHadQM1' : 'squark',
    'TRHadUM1' : 'stop',
    'TRHadDM1' : 'sbottom',
    "T5Gamma" : "gluino",
    "T5ZGamma" : "gluino",
    "T5HGamma" : "gluino",
    "T6Gamma" :    "squark",
    "TChipChimGamma" :  "chargino^pm_1 chargino^mp_1/neutralino_2",
    "T5g" : "gluino",
    "T5Zg" : "gluino",
    "T5Hg" : "gluino",
    "T6g" :    "squark",
    "TChipChimg" :  "chargino^pm_1 chargino^mp_1/neutralino_2",
    "TChipChimgg" :  "chargino^pm_1 chargino^mp_1/neutralino_2",
    "TSlepSlepAll" : "slepton",
    "TChipChimSlepSlepAll" :  "chargino^pm_1",
    "TChipChimSlepSlep" :  "chargino^pm_1",
    "TChiChipmSlep" :  "neutralino_2 chargino^pm_1"
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
        if '/'+key in outstr:
            outstr = outstr.replace('/'+key,'/'+rep)


    outstr = outstr.replace('-->','#rightarrow')
    outstr = outstr.lstrip().rstrip()
    return outstr

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
            logging.error('When searching for %s: Unknown decay format: %s' % \
                           ( inter, str(decays) ) )

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
    FIXME fix the "latex" mode, it is a "root" mode.
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
    FIXME fix the "latex" mode, it is a "root" mode.
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


def prettyTxname(txname,outputtype="root"):
    """
    Converts the txname string to the corresponding SUSY desctiption
    in latex form (using ROOT conventions)
    :param: txname (string) (e.g. 'T1')
    :param outputtype: root: return a ROOT string
                       latex: return a latex string
                       text: return a human readable string

    :return: string or latex string
             (e.g. pp #rightarrow #tilde{g} #tilde{g},
             #tilde{g} #rightarrow q q #tilde{#chi}_{1}^{0})
    """
    if not outputtype in [ "root", "latex", "text" ]:
        logging.error ( "Unknown output type: %s. Known types: root, latex, text" % outputtype )
        import sys
        sys.exit()

    latex=False
    if outputtype in [ "root", "latex" ]:
        latex=True

    prodString = prettyProduction(txname,latex)
    decayString = prettyDecay(txname,latex)
    if outputtype == "latex":
        prodString = "$" + prodString.replace("#","\\" ) + "$"
        decayString = "$" + decayString.replace("#","\\" ) + "$"

    if prodString and decayString:
        return prodString + ", " + decayString
    else:
        return None

def prettyTexAnalysisName ( prettyname, sqrts = None, dropEtmiss = False,
                            collaboration = None, anaid = None ):
    """ create good TeX version of pretty name
    :param sqrts: if not None, add <sqrts> TeV to name
    :param dropEtmiss: if True, then Etmiss gets dropped
    :param collaboration: if not None, prefix with collaboration name. if True and
                          anaid is given, then infer collaboration name from anaid
    :param anaid: analysis id. if given, then we also query a dictionary
    """

    prettyNames = { "ATLAS-SUSY-2013-02": "ATL multijet, 8 TeV",
        "ATLAS-SUSY-2013-15": "ATL 1$\ell$ stop, 8 TeV",
        "ATLAS-SUSY-2016-07": "ATL multijet, 13 TeV",
        "ATLAS-SUSY-2016-16": "ATL 1$\ell$ stop, 13 TeV",
        "CMS-SUS-13-012": "CMS multijet, 8 TeV",
        "CMS-SUS-16-050": "CMS $0\ell$ stop, 13 TeV"
    }
    if anaid != None and anaid in prettyNames:
        return prettyNames[anaid]
    if anaid != None and collaboration == True:
        collaboration = "CMS"
        if "ATLAS" in anaid:
            collaboration = "ATL"
    if prettyname == None:
        prettyname = "???"
    pn = prettyname.replace(">","$>$").replace("<","$<$")
    pn = pn.replace("0 or $>$=1 leptons +","" )
    pn = pn.replace("photon photon","$\gamma\gamma$" )
    pn = pn.replace("SF OS","SFOS" )
    pn = pn.replace("jet multiplicity","n$_{jets}$" )
    pn = pn.replace("Higgs","H" )
    pn = pn.replace("searches in","to" )
    pn = pn.replace("same-sign","SS" )
    pn = pn.replace("Multilepton","multi-l" )
    pn = pn.replace("multilepton","multi-l" )
    pn = pn.replace("leptons","l's" )
    pn = pn.replace("lepton","l" )
    pn = pn.replace("1L","1$\ell$" )
    pn = pn.replace("0L","0$\ell$" )
    pn = pn.replace("1 l","1$\ell$" )
    pn = pn.replace("0 leptons","0$\ell$" )
    pn = pn.replace("dilepton","di\-l" )
    pn = pn.replace("productions with decays to","prod, to ")
    pn = pn.replace("photon","$\gamma$" )
    pn = pn.replace("Photon","$\gamma$" )
    pn = pn.replace("-$>$","$\\rightarrow$" )
    pn = pn.replace("final states","")
    pn = pn.replace("final state","")
    if dropEtmiss:
        for etm in [ "ETmiss", "Etmiss", "MET" ]:
            pn = pn.replace(" + "+etm,"")
            pn = pn.replace("+ "+etm,"")
            pn = pn.replace("+"+etm,"")
            pn = pn.replace(etm,"")
    pn = pn.replace("ETmiss","$\\not{\!\!E}_T$")
    pn = pn.replace("Etmiss","$\\not{\!\!E}_T$")
    pn = pn.replace("MET","$\\not{\!\!E}_T$")
    pn = pn.replace("M_CT","M$_CT$" )
    pn = pn.replace("alpha_T","$\\alpha_T$" )
    if len(pn)>0 and pn[-1]==")":
        pos = pn.rfind ( "(" )
        pn = pn[:pos]
    pn = pn.strip()
    if sqrts != None:
        try:
            sqrts = sqrts.asNumber(TeV)
        except Exception as e:
            pass
        pn += ", %d TeV" % sqrts
    if collaboration != None:
        pn = collaboration + " " + pn
    return pn

def prettyAxes(txname,axes):
    """
    Converts the axes string to the axes labels (plus additional constraints)
    in latex form (using ROOT conventions)
    :param txname: txname string  (e.g. 'T1')
    :param axes: axes string (e.g. '[[x, y], [1150, x, y]]')

    :return: dictionary with the latex labels
             (e.g. {'x' : m_{#tilde{g}}, 'y' : m_{#tilde{#chi}_{1}^{0}}
             'constraints' : [m_{#tilde{l}} = 0.05*m_{#tilde{g}} + 0.95*m_{#tilde{#chi}_{1}^{0}}]})
    """

    #Build axes object (depending on symmetric or asymmetric branches:
    axes = eval(axes)
    if txname == 'THSCPM2b':
        return ['m_{#tilde{#tau}} = (x,y)', ]
    if txname == 'THSCPM4':
        return ['m_{#tilde{q}} = x, m_{#tilde{#chi}_{1}^{#pm}} = (y,1e-22)', ]
    if txname == 'THSCPM5':
        return ['m_{#tilde{q}} = x, m_{#tilde{#chi}_{1}^{0}} = x-100',
                'm_{#tilde{#tau}} = (y,1e-22)' ]
    if txname == 'THSCPM7':
        return ['m_{#tilde{q}} = x, m_{#tilde{#chi}_{1}^{0}} = x-100',
                'm_{#tilde{#chi}_{1}^{#pm}} = (y,1e-22)' ]
    if txname == 'THSCPM6':
        return ['m_{#tilde{q}} = x, m_{#tilde{#chi}_{1}^{0}} = x-100',
                'm_{#tilde{#tau}} = (y,1e-22)' ]
    if txname == 'TGQ':
        return ['m_{#tilde{g}} = x, m_{#tilde{q}} = 0.96*x',
                    'm_{#tilde{#chi}_{1}^{0}} = y']
    if txname == 'T3GQ':
        ret = ['m_{#tilde{g}} = x, m_{#tilde{q}} = y',
               'm_{#tilde{#chi}_{1}^{0}} = %s' % str(axes[0][1]) ]
        return ret
    if txname == 'T5GQ':
        ret = ['m_{#tilde{q}} = x, m_{#tilde{g}} = y',
               'm_{#tilde{#chi}_{1}^{0}} = %s' % str(axes[1][1]) ]
        return ret
    if txname == 'TChiChiSlepSlep':
        return ['m_{#tilde{#chi}_{3}^{0}} = x+80.0, m_{#tilde{#chi}_{2}^{0}} = x+75.0',
                    'm_{#tilde{#l}} = x-y+80.0',
                    'm_{#tilde{#chi}_{1}^{0}} = x']
    if txname in [ "TGQ12" ] and axes[0][1] == axes[1][1]:
        ret = ['m_{#tilde{g}} = x, m_{#tilde{q}} = y',
               'm_{#tilde{#chi}_{1}^{0}} = %s' % str(axes[0][1]) ]
        return ret
    if axes[0] != axes[1]:
        logging.error('Asymmetric branches are not yet automatized.')
        return "N/A"

    ax = axes[0]
    if len(ax) > 3:
        logging.error("Nice axes with more than one \
        intermetiate particle is not available.")
        return "N/A"

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
    def roundme ( x ):
        if type(x) == float:
            if x != 0.:
              round_to_n = lambda x, n: round(x, -int(floor(log10(x))) + (n - 1))
              r = round_to_n(x,2)
            else:
              r = x
            return r
        if type(x) == tuple:
            tmp = [ roundme(i) for i in x ]
            return tuple(tmp)
        return x

    for i,eq in enumerate(ax):
        eq = roundme(eq )
        axStr = massStrings[i].strip()+'='+str(eq)
        niceAxes.append(axStr.replace("'",""))

    return niceAxes

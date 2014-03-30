#!/usr/bin/env python

'''
.. module:: dictionaries
   :synopsis: Module contains all hard coded dictionaries needed for several descriptions

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


'''
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

prettyparticle = {
	'g': '#tilde{g}',
	'q': '#tilde{q}',
	'b': '#tilde{b}',
	't': '#tilde{t}',
	'c0': '#tilde{#chi}^{0}_{1}',
	'cpm': '#tilde{#chi}^{#pm}_{1}',
	'l': '#tilde{l}',
	'c0cpm': '#tilde{#chi}^{0}_{2}#tilde{#chi}^{#pm}_{1}'
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

decay = { 'T1': '#tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{1}', 
	'T1bbbb': '#tilde{g} #rightarrow b#bar{b} #tilde{#chi}^{0}_{1}',
	'T1tttt': '#tilde{g} #rightarrow t#bar{t} #tilde{#chi}^{0}_{1}',
	'T1gg':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow #gamma#tilde{#chi}^{0}_{1})',
	'T1lg':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow#gamma#tilde{#chi}^{0}_{1}|#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
	'T1lnu':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm} #rightarrow l^{#pm}#nu #tilde{#chi}^{0}_{1})',
    'T1lh':'#tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{2},#tilde{#chi}^{0}_{2} #rightarrow l^{+}l^{-}#tilde{#chi}^{0}_{1}',
    'T2':'#tilde{q} #rightarrow q #tilde{#chi}^{0}_{1}',
	'T2FVttcc': '#tilde{t} #rightarrow c #tilde{#chi}^{0}_{1}',
    'T2llnunubb': '#tilde{t} #rightarrow l #nu b #tilde{#chi}^{0}_{1}',
    'T2bb':'#tilde{b} #rightarrow b #tilde{#chi}^{0}_{1}',
    'T2bw':'#tilde{t} #rightarrow b (#tilde{#chi}^{#pm}_{1} #rightarrow W #tilde{#chi}^{0}_{1})',
    'T2ttww': '#tilde{b} #rightarrow tW #tilde{#chi}^{0}_{1}',
    'T2tt': '#tilde{t} #rightarrow t #tilde{#chi}^{0}_{1}',
    'T3w': '#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1} |#tilde{#chi}^{0}_{1})',
    'T3wb':'#tilde{g} #rightarrow b#bar{b}(W)#tilde{#chi}^{0}_{1}',
    'T3lh':'#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow l^{+}l^{-}#tilde{#chi}^{0}_{1})',
    'T3tauh':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{2}#rightarrow #tau #tau #tilde{#chi}^{0}_{1} |#tilde{#chi}^{0}_{1})',
    'T5WW':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
    'T5wg':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow#gamma#tilde{#chi}^{0}_{1}|#tilde{#chi}^{#pm}_{1}#rightarrow W#tilde{#chi}^{0}_{1})',
    'T5WH':'#tilde{g} #rightarrow q#bar{q} #tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1} H#tilde{#chi}^{0}_{1} ',
    'T5gg':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{0}_{2}#rightarrow #gamma#tilde{#chi}^{0}_{1})',
    'T5lnu':'#tilde{g} #rightarrow q#bar{q}(#tilde{#chi}^{#pm} #rightarrow l^{#pm}#nu #tilde{#chi}^{0}_{1})',
    'T5ZZ':'#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow Z #tilde{#chi}^{0}_{1})',
    'T5ZZInc':'#tilde{#chi}^{0}_{2} #rightarrow Z #tilde{#chi}^{0}_{1}',
    'T5zzgmsb':'#tilde{g} #rightarrow q#bar{q} (#tilde{#chi}^{0}_{2}#rightarrow Z #tilde{#chi}^{0}_{1})',
    'T5tttt':'#tilde{g} #rightarrow t(#tilde{t} #rightarrow t#tilde{#chi}^{0}_{1})',
    'T6ttww': '#tilde{b} #rightarrow tW #tilde{#chi}^{0}_{1}',
    'T6ttHH': '#tilde{t} #rightarrow tH #tilde{#chi}^{0}_{1}',
    'T6ttzz': '#tilde{t}_{2} #rightarrow tilde{t}_{1}Z #rightarrow #tilde{#chi}^{0}_{1}t',
    'T6bbWW':'#tilde{t} #rightarrow b(#tilde{#chi}^{+} #rightarrow W#tilde{#chi}^{0}_{1})',
    'T6bbZZ':'#tilde{b} #rightarrow bZ #tilde{#chi}^{0}_{1}',
    'T7btW':'#tilde{g} #rightarrow btW#tilde{#chi}^{0}_{1}',
    'T7btbtWW':'#tilde{g} #rightarrow b(#tilde{b} #rightarrow t(#tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1}))',
    'TChiwz':'#tilde{#chi}^{#pm} #tilde{#chi}^{0}_{2} #rightarrow W Z #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1}',
    'TChizz':'#tilde{#chi}^{0}_{3} #tilde{#chi}^{0}_{2} #rightarrow Z Z #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1}',
    'TChiSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow l l l #nu #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiNuSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow l l l #nu #tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiSlepSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm}_{1} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmHW':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow W#tilde{#chi}^{0}_{1} H#tilde{#chi}^{0}_{1} ',
    'TChiChipmSlepL':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmSlepSlep':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow lll #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmSlepStau':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow ll#tau #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChiChipmStauStau':'#tilde{#chi}^{0}_{2} #tilde{#chi}^{#pm} #rightarrow #tau#tau#tau #nu#tilde{#chi}^{0}_{1} #tilde{#chi}^{0}_{1} ',
    'TChipChimSlepSnu':'#tilde{#chi}^{+}#tilde{#chi}^{-} #rightarrow l^{+}l^{-}#nu#nu#tilde{#chi}^{0}_{1}#tilde{#chi}^{0}_{1}',
    'TSlepSlep':'#tilde{l} #rightarrow l #tilde{#chi}^{0}_{1}'
}

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
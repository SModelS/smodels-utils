#!/usr/bin/env python3

"""
.. module:: testAnalysisCombinations
   :synopsis: Testbed for llhd combinations, plots likelihods

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import sys
sys.path.insert(0, "../")

from smodels.tools import runtime
runtime._experimental = True
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory import decomposer
from smodels.tools.theoryPredictionsCombiner import TheoryPredictionsCombiner
from smodels.theory.model import Model
from smodels.share.models.SMparticles import SMList
from smodels.share.models.mssm import BSMList
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import fb, GeV
import unittest
import numpy as np
import os
import time
from smodels_utils.plotting import mpkitty as plt
from covariances.cov_helpers import getSensibleMuRange, computeLlhdHisto, addJitter, withinMuRange, createLine
from colorama import Fore, Cursor

dbpath = [ "../../smodels-database/" ]
# dbpath = [ "official" ]
dbpath = [ "official+fastlim+nonaggregated" ]

def getSetupTStauStau():
    """ ATLAS-SUSY-2018-04, pyhf """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2018-04' ]
    dsids = [ 'SRhigh', 'SRlow' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-04' ]

    # dsids = [ "SRtN2", "6NJet8_1000HT1250_200MHT300", "3NJet6_1250HT1500_300MHT450", "ar8" ]
    # dsids = [ 'SRWZ_6', 'SRWZ_7', 'SRWZ_8', 'SRWZ_9' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    jsonf = list ( comb_results[0].globalInfo.jsonFiles.keys() )
    ret = { "slhafile": "TStauStau_220_151_220_151.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-6., 10. ),
            "dictname": "staustau.dict",
            "output": "combo_1804.png"
    }
    if "simplified" in jsonf[0]:
        ret["output"]="combo_1804simplified.png"
        ret["label"]="simplified"
    return ret

def getSetupRExp():
    """ ATLAS-CONF-2013-037, CMS-SUS-13-012 """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-CONF-2013-037', 'CMS-SUS-13-012' ]
    dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "gluino_squarks.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-4., 6. ),
            "dictname": "rexp.dict",
            "output": "debug_rexp.png"
    }
    return ret

def getSetupFilter():
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2019-09', 'ATLAS-SUSY-2018-12', "CMS-SUS-12-024" ]
    dsids = [ 'SRATT', 'SRWZ_14', 'MET4_HT4_nb3' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "gluino_squarks.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-4., 6. ),
            "dictname": "rexp.dict",
            "output": "debug_rexp.png"
    }
    return ret

def getSetupSabine():
    """ ATLAS-SUSY-2018-41 and CMS-SUS-20-001 """
    database = Database( dbpath[0] )
    dTypes = ["all"]
    anaids = [ 'ATLAS-SUSY-2018-41-eff', 'CMS-SUS-20-001' ]
    anaids = [ 'CMS-SUS-20-001' ]
    dsids = [ 'all' ]
    # dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-41-eff' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "Mtwo700.0_muPos100.0.slha",
            "SR": exp_results,
            "comb": comb_results,
#            "murange": (-70., 15. ),
            "murange": (-10., 10. ),
            "dictname": "rsabine.dict",
            "output": "sabine.png"
    }
    return ret

def getSetupSabine2():
    """ ATLAS-SUSY-2016-06, CMS-EXO-19-010 """
    database = Database( dbpath[0] )
    dTypes = ["all"]
    anaids = [ 'ATLAS-SUSY-2016-06', 'CMS-EXO-19-010' ]
    # dsids = [ 'all' ]
    dsids = [ 'SR_nlay6p', 'SR_EW' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ ] #  'ATLAS-SUSY-2018-41-eff' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "binoWino100.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-1.5, 1.5 ),
            "dictname": "rsabine2.dict",
            "output": "sabine2.png"
    }
    return ret

def getSetup19006():
    """ CMS-SUS-19-006 (sr combo) """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit"]
    anaids = [ 'CMS-SUS-19-006' ]
    dsids = [ 'all' ]
    # dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-19-006-agg' ]
    # dsids = [ 'AR1', 'AR2' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    # comb_results = []
    ret = { "slhafile": "T1_1250_250_1250_250.slha",
            "SR": exp_results,
            "comb": comb_results,
            # "murange": (-1.5, 1. ),
            "murange": (-.09, .13 ),
            "dictname": "19006.dict",
            "output": "19006.png"
    }
    return ret


def getSetupJamie():
    """ a few efficiency maps and a TPC combination """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2016-07', 'ATLAS-SUSY-2013-02', 'CMS-SUS-13-012' ]
    # anaids = [ 'ATLAS-SUSY-2016-07' ]
    # dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    dsids = [ '2j_Meff_3600', 'SR2jt', 'SR_6NJet8_500HT800_450MHTinf', 'SR_8NJetinf_1000HT1250_200MHTinf', '6NJet8_500HT800_450MHTinf', '8NJetinf_1000HT1250_200MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    # exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2016-07', 'ATLAS-SUSY-2013-02', 'CMS-SUS-13-012' ]
    anaids = [ 'ATLAS-SUSY-2016-07' ]
    dsids = [ '2j_Meff_3600', 'SR2jt', '6NJet8_500HT800_450MHTinf', '8NJetinf_1000HT1250_200MHTinf' ]
    # dsids = [ '2j_Meff_3600', 'SR2jt', 'SR_6NJet8_500HT800_450MHTinf', 'SR_8NJetinf_1000HT1250_200MHTinf', '6NJet8_500HT800_450MHTinf', '8NJetinf_1000HT1250_200MHTinf' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    comb_results = []
    ret = { "slhafile": "100377801.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -30., 50. ),
            "dictname": "jamie1.dict",
            "expected": False,
            "output": "jamie1.png"
    }
    if ret["expected"]==False:
        ret["murange"] = ( -15., 65. )
    ret["addjitter"]=0.008
    return ret


def getSetupJamie2():
    """ ATLAS-SUSY-2016-07, CMS-SUS-19-006, ATLAS-SUSY-2013-02, CMS-SUS-13-012 """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2016-07', 'ATLAS-SUSY-2013-02', 'CMS-SUS-13-012', 'CMS-SUS-19-006-ma5', 'CMS-SUS-19-006' ]
    dsids = [ '2j_Meff_2400', 'SR2jt', 'SR76', 'SR26', 'SR120', '3NJet6_500HT800_600MHTinf', '6NJet8_500HT800_450MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    #exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2016-07', 'ATLAS-SUSY-2013-02', 'CMS-SUS-13-012' ]
    anaids = [ 'ATLAS-SUSY-2016-07' ]
    dsids = [ '2j_Meff_3600', 'SR2jt', '6NJet8_500HT800_450MHTinf', '8NJetinf_1000HT1250_200MHTinf' ]
    # dsids = [ '2j_Meff_3600', 'SR2jt', 'SR_6NJet8_500HT800_450MHTinf', 'SR_8NJetinf_1000HT1250_200MHTinf', '6NJet8_500HT800_450MHTinf', '8NJetinf_1000HT1250_200MHTinf' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    comb_results = []
    ret = { "slhafile": "111928145.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -10., 20. ),
            "dictname": "jamie2.dict",
            "expected": True,
            "output": "jamie2.png"
    }
    if ret["expected"]==False:
        ret["murange"] = ( -10., 20. )
    ret["addjitter"]=0.008
    return ret

def getSetupTimotheeSR():
    """ CMS-SUS-20-001 (UL), ATLAS-SUSY-2019-09 (best SR) """
    database = Database( dbpath[0] )
    dTypes = ["all"]
    anaids = [ 'CMS-SUS-20-001', 'ATLAS-SUSY-2019-09' ]
    dsids = [ None, "SRWZ_5" ]
    tmp = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    exp_results = []
    for t in tmp:
        if t.id() == "ATLAS-SUSY-2019-09" and t.datasets[0].dataInfo.dataId == None:
            continue
        exp_results.append ( t )

    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2019-09' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    comb_results = []
    ret = { "slhafile": "wino_Spectrum_160_50.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -.8, .3 ),
            "dictname": "timsr.dict",
            "expected": False,
            "output": "timsr.png"
    }
    if ret["expected"]==False:
        ret["murange"] = ( -.8, 1.3 )
    ret["addjitter"]=0.008
    ret["addjitter"]=0.008
    return ret

def getSetupBill():
    """ CMS-SUS-20-004 (UL), CMS-SUS-20-004 (combined) """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit" ]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ None ]
    tmp = database.getExpResults(analysisIDs=anaids, datasetIDs=dsids,
            dataTypes=dTypes, useNonValidated = True )

    exp_results = tmp

    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
            datasetIDs=dsids, dataTypes=dTypes, useNonValidated = True )
    ret = { "slhafile": "TChiHH_300_0_300_0.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -.8, 1.5 ),
            "dictname": "20004.dict",
            "expected": False,
            "output": "20-004.png"
    }
    ret["addjitter"]=0.002
    ret["addjitter"]=0.002
    ret["rewrite"]=True
    ret["plotproduct"]=False
    return ret

def getSetupBill2():
    """ CMS-SUS-20-004 (UL), CMS-SUS-20-004 (combined) """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit" ]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ None ]
    tmp = database.getExpResults(analysisIDs=anaids, datasetIDs=dsids,
            dataTypes=dTypes, useNonValidated = True )

    exp_results = tmp
    # exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
            datasetIDs=dsids, dataTypes=dTypes, useNonValidated = True )
    ret = { "slhafile": "TChiHH_750_0_750_0.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -1., 4. ),
            "dictname": "20004b.dict",
            "expected": False,
            "output": "20-004b.png"
    }
    ret["addjitter"]=0.002
    ret["addjitter"]=0.002
    ret["rewrite"]=True
    ret["logy"]=False
    ret["normalize"]=True
    ret["plotproduct"]=False
    return ret

def getSetupBill3():
    """ CMS-SUS-20-004 (UL), CMS-SUS-20-004 (combined) """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit" ]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ None ]
    tmp = database.getExpResults(analysisIDs=anaids, datasetIDs=dsids,
            dataTypes=dTypes, useNonValidated = True )

    exp_results = tmp
    # exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-20-004' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
            datasetIDs=dsids, dataTypes=dTypes, useNonValidated = True )
    ret = { "slhafile": "TChiHH_450_0_450_0.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -1., 3. ),
            "dictname": "20004c.dict",
            "expected": False,
            "output": "20-004c.png"
    }
    ret["addjitter"]=0.002
    ret["addjitter"]=0.002
    ret["rewrite"]=True
    ret["logy"]=False
    ret["normalize"]=True
    ret["plotproduct"]=False
    return ret


def getSetupTimotheeCombined():
    """ CMS-SUS-20-001, ATLAS-SUSY-2019-09 """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit"]
    anaids = [ 'CMS-SUS-20-001' ]
    dsids = [ 'all' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    # exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2019-09' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    # comb_results = []
    ret = { "slhafile": "wino_Spectrum_160_50.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -.2, .5 ),
            "dictname": "timc.dict",
            "expected": False,
            "output": "timc.png"
    }
    if ret["expected"]==False:
        ret["murange"] = ( -.2, .5 )
    ret["addjitter"]=0.008
    ret["addjitter"]=0.008
    return ret

def getSetup16050():
    """ CMS-SUS-16-050 combined with SL """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit"]
    anaids = [ 'CMS-SUS-16-050' ]
    dsids = [ 'all' ]
    # dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    # exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-16-050' ]
    # dsids = [ 'AR1', 'AR2' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    # comb_results = []
    ret = { "slhafile": "T2tt_880_150_880_150.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-.6, .9 ),
            "dictname": "16050.dict",
            "output": "16050.png"
    }
    return ret

def getSetup16050agg():
    """ CMS-SUS-16-050-agg combined with SL """
    database = Database( dbpath[0] )
    dTypes = ["upperLimit"]
    anaids = [ 'CMS-SUS-16-050' ]
    dsids = [ 'all' ]
    # dsids = [ 'SRtN3', '3NJet6_1000HT1250_600MHTinf' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    exp_results = []

    dTypes = ["efficiencyMap"]
    anaids = [ 'CMS-SUS-16-050-agg' ]
    # dsids = [ 'AR1', 'AR2' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                          datasetIDs=dsids, dataTypes=dTypes)
    # comb_results = []
    ret = { "slhafile": "T2tt_880_150_880_150.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": (-3, 3. ),
            "dictname": "16050agg.dict",
            "output": "16050agg.png"
    }
    return ret

def getSetupTChiWZ():
    """ ATLAS-SUSY-2017-03 and ATLAS-SUSY-2018-06 (pyhf) """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2018-06'  ]
    dsids = [ 'SR2l_Int', 'SR_ISR', 'SR_low' ]
    dsids = [ 'SR_ISR', 'SR_low' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-06' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "TChiWZ_460_230_460_230.slha",
            "SR": exp_results,
            "comb": comb_results,
            "dictname": "chiwz.dict",
            "murange": ( -4., 12. ),
            "output": "combo_1806.png"
    }
    return ret

def getSetupT6bbHH():
    """ ATLAS-SUSY-2018-31 (pyhf) """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2018-31', 'ATLAS-SUSY-2018-xx'  ]
    dsids = [ 'SRB', 'SRA_M' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-31' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    jsonf = list ( comb_results[0].globalInfo.jsonFiles.keys() )
    ret = { "slhafile": "T6bbHH_504_241_111_504_241_111.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -1.5, 2. ),
            "dictname": "t6bbhh.dict",
            "output": "combo_1831.png",
    }
    if "simplif" in jsonf[0]:
        ret["output"] = "combo_1831simplified.png"
        ret["label"]="simplified"
    return ret

def getSetupUL():
    """ a combination with an UL likelihood """
    database = Database( dbpath[0] )
    dTypes = ["all"]
    anaids = [ 'ATLAS-SUSY-2018-40' ]
    dsids = [ 'MultiBin1', 'MultiBin2', 'MultiBin3', 'SingleBin', None ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2018-31x' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    jsonf = [ "x" ]
    if len(comb_results)>0:
        jsonf = list ( comb_results[0].globalInfo.jsonFiles.keys() )
    ret = { "slhafile": "T6bbHH_504_241_111_504_241_111.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -1.5, 2. ),
            "dictname": "ul.dict",
            "output": "ul_1840.png",
    }
    if "simplif" in jsonf[0]:
        ret["output"] = "combo_1840simplified.png"
        ret["label"]="simplified"
    return ret

def getSetupTChiWZ09():
    """ ATLAS-SUSY-2017-03 and ATLAS-SUSY-2019-09 (pyhf) """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2017-03', 'ATLAS-SUSY-2019-09'  ]
    #anaids = [ 'ATLAS-SUSY-2019-09'  ]
    dsids = [ 'SR2l_Int', 'SRWZ_10', 'SRWZ_20' ]
    #dsids = [ 'all' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)

    anaids = [ 'ATLAS-SUSY-2019-09' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "TChiWZ_460_230_460_230.slha",
            "SR": exp_results,
            "comb": comb_results,
            "dictname": "1909.dict",
            "output": "combo_1909.png",
#"murange": (-4,5),
            "murange": (-1,2),
    }
    return ret

def getSetupTChiWH():
    """ ATLAS-SUSY-2017-01, ATLAS-SUSY-2019-08 """
    database = Database( dbpath[0] )
    dTypes = ["efficiencyMap"]
    anaids = [ 'ATLAS-SUSY-2017-01', 'ATLAS-SUSY-2019-08'  ]
    dsids = [ 'SRHad-Low', 'SR_MM_Low_MCT', 'SR_HM_Med_MCT' ]
    exp_results = database.getExpResults(analysisIDs=anaids,
                      datasetIDs=dsids, dataTypes=dTypes, useNonValidated=True )

    anaids = [ 'ATLAS-SUSY-2019-08' ]
    dsids = [ 'all' ]
    comb_results = database.getExpResults(analysisIDs=anaids,
                                         datasetIDs=dsids, dataTypes=dTypes)
    ret = { "slhafile": "TChiWH_525_80_525_80.slha",
            "SR": exp_results,
            "comb": comb_results,
            "murange": ( -2.5, 2.5 ),
            "dictname": "1908.dict",
            "output": "combo_1908.png",
    }
    return ret

def writeDictFile ( dictname, llhds, times, fits, uls, setup ):
    """ write out the likelihoods.dict file
    :param dictname: name of file, e.g. likelihoods.dict
    """
    g = open ( dictname, "wt" )
    g.write ( "llhds={\n" )
    for Id,l in llhds.items():
        sl="{"
        for k,v in l.items():
            sl+=f"{k:.3f}: {v:.3g}, "
        if len(sl)>3:
            sl=sl[:-2]+"}"
        g.write ( f"'{Id}': {sl},\n" )
    g.write("}\n" )
    g.write("times={" )
    for i,(k,v) in enumerate(times.items() ):
        if i > 0:
            g.write ( ", " )
        g.write ( f"'{k}': {v:.3f}" )
    g.write("}\n")
    g.write("fits="+str(fits)+"\n" )
    g.write("uls="+str(uls)+"\n" )
    setup.pop("SR")
    setup.pop("comb")
    g.write("setup="+str(setup)+"\n" )
    g.close()


def getLlhdAt ( prodllhd, ulmu ):
    ret = 1.0
    dist=float("inf")
    for k,v in prodllhd.items():
        d = (k-ulmu)**2
        if d < dist:
            dist = d
            ret = v
    return ret

def plotLlhds ( llhds, fits, uls, setup ):
    """ plot the likelihoods in llhds,
        additional stuff in fits, setup is the setup dictionary
    :param fits: dictionary that contains ulmu, mu_hat
    :param setup: dictionary that contains slhafile, and more
    """
    alllhds = []
    colors = {}
    for Id,l in llhds.items():
        if Id == "combined":
            continue
        args = { "ls": "-" }
        if "sr combo" in Id or "pyhf combo" in Id:
            args["linewidth"]=2
            args["c"]="r"
        alllhds += list( l.values() )
        yv = list ( l.values() )
        if setup["addjitter"]:
            jitter = .015
            if type(setup["addjitter"])==float:
                jitter=setup["addjitter"]
            addJitter ( yv, jitter )
        x = plt.plot ( l.keys(), yv, label=Id, **args )
        colors[Id] = x[0].get_color()
    prodllhd=llhds["combined"]
    totS = sum(prodllhd.values())
    if setup["normalize"]==False:
        totS=1.
    for k,v in prodllhd.items():
        prodllhd[k]=prodllhd[k]/totS
    llmin, llmax = 0., 1.
    if len(alllhds)>0:
        llmin = min ( alllhds )
        llmax = max ( alllhds )

    prody = list ( prodllhd.values() )
    if setup["addjitter"] and False:
        addJitter ( prody )
    if setup["plotproduct"]:
       plt.plot ( prodllhd.keys(), prody, c="k", label=r"$\Pi_i l_i$ [tpc]" )

    if "mu_hat" in fits:
        mu_hat = fits["mu_hat"]
        sigma_mu = fits["sigma_mu"]
        ulmu = fits["ulmu"]
        r = fits["r"]
        rexp = fits["rexp"]
        lmax = max ( prodllhd.values() )
        print ( f"[testAnalysisCombinations] product: muhat={mu_hat:.2g} sigma_mu={sigma_mu:.3g} lmax={lmax:.2g} ulmu={ulmu:.2f} r={r:.2f} rexp={rexp:.2f}" )
        # mu_hat = 1.
        ax = plt.gca()
        if setup["plotproduct"]:
            if withinMuRange ( mu_hat, setup["murange"] ):
                plt.plot ( [ mu_hat ]*2, [ llmin, .95 * lmax ], linestyle="-.", c="k", label=rf"$\hat\mu$ ($\Pi_i l_i$) [tpc:{mu_hat:.2f}]" )
            else:
                plt.text ( .6, -.11, rf"$\hat\mu$ ($\Pi_i l_i$) [tpc:{mu_hat:.2f}] (off chart)", transform=ax.transAxes, fontsize=9, c="gray" )
        llhd_ulmu = getLlhdAt ( prodllhd, ulmu )

        if setup["plotproduct"]:
            if withinMuRange ( ulmu, setup["murange"] ):
                plt.plot ( [ ulmu ]*2, [ llmin, .95 * llhd_ulmu ], linestyle="dotted",
                       c="k", label=rf"ul$_\mu$ ($\Pi_i l_i$) [tpc:{ulmu:.2f}]" )
            else:
                plt.text ( -.1, -.11, rf"ul$_\mu$ ($\Pi_i l_i$) [tpc:{ulmu:.2f}] (off chart)", transform=ax.transAxes, fontsize=9, c="gray" )

    if True and "llhd_combo(ul)" in fits:
        # print ( f"[testAnalysisCombinations] combo ul_mu {ulmu:.2f}" )
        llhdul = fits["llhd_combo(ul)"]
        # print ( "[testAnalysisCombinations] llhd at", fits["muhat_combo"], "(combo) is", llhdul )
        srcombo = " (sr combo)"
        if fits["llhdtype"]=="pyhf":
            srcombo = " (pyhf combo)"
        if withinMuRange ( fits["ul_combo"], setup["murange"] ):
            line = { "x": [ fits["ul_combo"] ] *2, "y": [ llmin, 1.05* llhdul ] }
            plt.plot ( line["x"], line["y"], linestyle="dotted", c="r", label=rf"ul$_\mu${srcombo}: {fits['ul_combo']:.2f}" )
        lmax = fits["lmax_combo"]
        # lmax = llmax
        if withinMuRange ( fits["muhat_combo"], setup["murange"] ):
            line = createLine ( fits["muhat_combo"], llmin, lmax, True )
            # plt.plot ( [ fits["muhat_combo"] ]*2, [ llmin, .95*lmax], linestyle="-.", c="r", label=r"$\hat\mu$ (sr combo)" )
            plt.plot ( line["x"], line["y"], linestyle="-.", c="r", label=rf"$\hat\mu${srcombo}: {fits['muhat_combo']:.2f}" )

    if True and "llhd_ul" in fits:
        # print ( f"[testAnalysisCombinations] ul ul_mu {ulmu:.2f}" )
        llhdul = [ fits["llhd_ul"]]
        # print ( "llhd at", fits["ul_ul"], "is", llhdul )
        plt.plot ( [ fits["ul_ul"] ] *2, [ llmin, llhdul ], linestyle="dotted", c="r", label=r"ul$_\mu$ (sr combo ul)" )
        lmax = llmax
        plt.plot ( [ fits["muhat_ul"] ] *2 , [ llmin, .95 * lmax ], linestyle="-.", c="r", label=r"$\hat\mu$ (ul)" )

    for Id,values in uls.items():
        ul = values [ "ulmu" ]
        if not withinMuRange ( ul, setup["murange"] ):
            continue
        l = values [ "lulmu" ]
        label = r"ul$_\mu$ (%s)" % Id
        # label = None
        if not "combo" in Id:
            plt.plot ( [ ul ] *2, [ llmin, l ], linestyle="dotted", c=colors[Id], label= label )
        muhat = values["muhat"]
        lmax = values["lmax"]
        # if muhat < 0.:
        label = f"$\hat\mu$ ({Id})"
        if not "combo" in Id:
            plt.plot ( [ muhat ] *2, [ llmin, lmax ], linestyle="-.", \
                        c=colors[Id], label= label )

    slha = setup["slhafile"]
    p = slha.find("_")
    if False: # p > 0:
        slha = slha[:p]
    label = ""
    if "label" in setup:
        label = setup["label"]+" "
    plt.title ( f"{label}likelihoods for {slha}" )
    plt.legend()
    # plt.legend(bbox_to_anchor=(1.1, 1.05)) # place outside
    plt.xlabel ( r"$\mu$" )
    output = "combo.png"
    if "output" in setup:
        output = setup["output"]
    if setup["logy"]:
        plt.yscale ( "log" )
    plt.kittyPlot( output )
    print ( f"{Cursor.UP()}[testAnalysisCombinations] saved to {output}" )

def createLlhds ( tpreds, setup ):
    """ given the setup and tpreds, create llhds dicts
    """
    combiner = TheoryPredictionsCombiner( tpreds )
    combiner.computeStatistics()
    #xmin, xmax = getSensibleMuRange ( tpreds )
    # xmin, xmax = -6., 10.
    xmin, xmax = -2.5, 4.5
    if "murange" in setup:
        xmin, xmax = setup["murange"]

    expected = setup["expected"]
    normalize = setup["normalize"]
    times, llhds, sums, uls = {}, {}, {}, {}
    for t in tpreds:
        dId = "sr combo"
        if hasattr ( t.dataset.globalInfo, "jsonFiles" ):
            dId = "pyhf combo"
        if hasattr ( t.dataset, "dataInfo" ):
            dId = t.dataset.dataInfo.dataId
        #if dId.find("_")>-1:
        #    dId = dId[:dId.find("_")]
        if dId == None:
            dId = "UL"
        Id = f"{t.dataset.globalInfo.id}:{dId}"
        r = t.getRValue()
        xsec = t.xsection.value
        ul = t.getUpperLimit()
        eul = t.getUpperLimit(expected=True )
        ulmu = float ( ul / xsec )
        lulmu = t.likelihood ( mu = ulmu )
        eulmu = float ( eul / xsec )
        fmuhat = t.muhat( allowNegativeSignals = True )
        muhat = fmuhat
        lmax = t.likelihood ( mu = muhat )
        sigma_mu = t.sigma_mu( allowNegativeSignals = True )
        if type(muhat)==float:
            muhat = f"{muhat:.2g}"
        if type(sigma_mu)==float:
            sigma_mu = f"{sigma_mu:.2g}"
        print ( f"[testAnalysisCombinations] looking at {Id}:" )
        print ( f"  `- r={r:.2f} xsec={xsec} ul={ul} ulmu={ulmu:.2f}")
        print ( f"  `- muhat={muhat} sigma_mu={sigma_mu}", end=" ", flush=True )
        t0 = time.time()
        t.computeStatistics( expected = expected )
        lsm = t.lsm()
        #thetahat_sm = t.dataset.theta_hat
        # print("er", Id, "lsm", lsm, "thetahat_sm", thetahat_sm, "lmax", t.lmax() )
        l, S = computeLlhdHisto ( t, xmin, xmax, nbins = 100,
                normalize = normalize, equidistant=False, expected = expected )
        # print ( f">> ulmu({Id})={ulmu:.2f}, l={lulmu:.2g} S={S:.2f}" )
        uls[Id] = { "ulmu": ulmu, "eulmu": eulmu, "lulmu": lulmu/S, "muhat": fmuhat, "lmax": lmax/S }
        llhds[Id]=l
        sums[Id] = S
        t1 = time.time()
        times[Id]=(t1-t0)
    ret = { "llhds": llhds, "sums": sums, "times": times, "uls": uls }
    return ret

def readDictFile ( dictname ):
    """ read the dict file, as a cache """
    f = open ( dictname, "rt" )
    txt = f.read()
    f.close()
    try:
        exec(txt,globals())
    except Exception as e:
        print ( f"[testAnalysisCombinations] could not read dict file {dictname}, deleting" )
        os.unlink ( dictname )
        return [ None ]*3
    print ( f"[testAnalysisCombinations] recycling llhds from {dictname}, delete if you dont want that" )
    return llhds, times, fits, uls, setup

def addCombinedLlhds ( d, combiner, expected ):
    """ add the combined likelihoods to d """
    llhds = d["llhds"]
    firstAnaId=list(llhds.keys())[0]
    muvalues = list(llhds[firstAnaId].keys())
    combL = {}
    totllhd = 0.
    for mu in muvalues:
        llhd = combiner.likelihood ( mu=mu, expected=expected )
        if llhd != None:
            combL[mu]=llhd
            totllhd+=llhd
    d["llhds"]["combined"]=combL
    return d

def testAnalysisCombo( setup ):
    """ this method should simply test if the fake result and the
        covariance matrix are constructed appropriately
    :param setup: dictionary, describing setup
    """
    dictname = "llhds.dict"
    if not "rewrite" in setup:
        setup["rewrite"]=False
    if "dictname" in setup:
        dictname = setup["dictname"]
        if os.path.exists ( dictname ) and setup["rewrite"] == False:
            oldsetup = setup
            llhds, times, fits, uls, newsetup = readDictFile ( dictname )
            if llhds != None:
                plotLlhds ( llhds, fits, uls, setup )
                return

    exp_results = setup["SR"]
    comb_results = setup["comb"]
    slhafile = setup["slhafile"]
    from validation.validationHelpers import retrieveValidationFile
    retrieveValidationFile ( slhafile )
    model = Model(BSMparticles=BSMList, SMparticles=SMList)
    model.updateParticles(inputFile=slhafile)
    sigmacut = 0.005*fb
    mingap = 5.*GeV
    smstopos = decomposer.decompose(model, sigmacut, doCompress=True,
           doInvisible=True, minmassgap=mingap )
    expected = setup["expected"]
    tpreds = []
    llhds = {}
    totllhd = {}
    combine = []
    ernames = set ( [ x.globalInfo.id for x in exp_results ] )
    print ( f"[testAnalysisCombinations] {len(exp_results)} non-combined results:", ", ".join(ernames)  )
    fits = {}
    for er in exp_results:
        ts = theoryPredictionsFor(er, smstopos,
            combinedResults=False, useBestDataset=False, marginalize=False)
        print ( f"   --- {er.id()}:{len(er.datasets)}: {ts} single preds" )
        if ts == None:
            continue
        for t in ts:
            tpreds.append(t)
            combine.append(t)
            if t.dataset.dataInfo.dataId == None:
                lmax = t.lmax( allowNegativeSignals = True, expected = expected )
                muhat = t.muhat( allowNegativeSignals = True, expected = expected )
                fits["muhat_ul"] = muhat
                fits["lmax_ul"] = lmax
                print ( f"[testAnalysisCombinations] UL: {t.dataset.globalInfo.id}: muhat={muhat:.3f} lmax={lmax:.3g} ul={float(t.getUpperLimit()/t.xsection.value):.3g}" )
    for er in comb_results:
        ts = theoryPredictionsFor(er, smstopos,
            combinedResults=True, useBestDataset=False, marginalize=False)
        print ( f"   --- {er.id()}: {len(ts)} SR results, {len(ts)} comb results" )
        for t in ts:
            print ( f"   combined result {t.dataset.globalInfo.id}" )
            combine.append(t)
        # ts = tsc
        if ts == None:
            continue
        for t in ts:
            tpreds.insert(0,t) ## put them in front so they always have same color
        ull = ts[0].getUpperLimit()
        llhdtype = "SL"
        if hasattr ( er.globalInfo , "jsonFiles" ):
            llhdtype = "pyhf"
        if type(ull) != type(None):
            ul = float ( ull / ts[0].xsection.value )
            fits["ul_combo"] = ul
            fits["llhdtype"]=llhdtype
            llhd_ul = ts[0].likelihood (  ul, expected = expected )
            fits["llhd_combo(ul)"] = llhd_ul
        muhat = ts[0].muhat( allowNegativeSignals = True, expected = expected )
        print ( f"[testAnalysisCombinations] ul:{ul:.2g} llhd_ul:{llhd_ul} muhat:{muhat}" )
        fits["muhat_combo"] = muhat
        fits["lmax_combo"] = ts[0].lmax( allowNegativeSignals = True, expected= expected )
    nplots = 0

    d = createLlhds ( tpreds, setup )
    if len(combine)>0:
        print ( f"{Fore.GREEN}[testAnalysisCombinations] now combining {len(combine)} tpreds{Fore.RESET}" )
        combiner = TheoryPredictionsCombiner(combine)
        combiner.computeStatistics()
        r = combiner.getRValue()
        r = combiner.getRValue( expected=True )
        fmh = combiner.findMuHat(expected=expected,
                allowNegativeSignals=True, extended_output=True)
        mu_hat, sigma_mu, lmax = fmh["muhat"], fmh["sigma_mu"], fmh["lmax"]
        ulmu = combiner.getUpperLimitOnMu( expected = expected )
        r = combiner.getRValue()
        rexp = combiner.getRValue( expected = True )
        fits.update ( { "mu_hat": mu_hat, "ulmu": ulmu, "lmax": lmax,
                        "r": r, "rexp": rexp, "expected": expected,
                        "sigma_mu": sigma_mu } )
        addCombinedLlhds ( d, combiner, expected=expected )

    llhds = d["llhds"]
    sums = d["sums"]
    times = d["times"]
    uls = d["uls"]
    if len(comb_results)>0 and len(ts)>0 and "llhd_combo(ul)" in fits:
        Id = f"{ts[0].dataset.globalInfo.id}:sr combo"
        if hasattr ( ts[0].dataset.globalInfo, "jsonFiles" ):
            Id = f"{ts[0].dataset.globalInfo.id}:pyhf combo"
        if Id in sums:
            S=sums[Id]
            fits["llhd_combo(ul)"] = fits["llhd_combo(ul)"] / S
            fits["lmax_combo"] = fits["lmax_combo"] / S

    plotLlhds ( llhds, fits, uls, setup )
    if len(tpreds)==0:
        print ( f"[testAnalysisCombinations] no tpreds found to combine" )
        sys.exit()
    writeDictFile ( dictname, llhds, times, fits, uls, setup )

def runSlew( rewrite = False ):
    """ run them all
    :param rewrite: if true, rewrite the dicts, rerun the computations
    """
    print ( "[testAnalysisCombinations] run all functions" )
    import sys
    funcs = dir( sys.modules[__name__] )
    setups = []
    for f in funcs:
        if f.startswith ( "getSetup" ) and not f.endswith ( "etup" ):
            setups.append ( f )
    for f in setups:
        print ( f"[testAnalysisCombinations] running {f}" )
        setup = eval( f"{f}()" )
        setup["rewrite"]=rewrite
        testAnalysisCombo( setup )
    sys.exit()

def addDefaults ( setup ):
    default = {}
    default["rewrite"]=True
    default["expected"]=False
    default["addjitter"]=True
    default["normalize"]=True
    default["logy"]=False
    default["plotproduct"]=True
    for k,v in default.items():
        if not k in setup:
            setup[k]=v
    return setup

def getSetup( which="TChiWZ09" ):
    name = f"getSetup{which}"
    if not name in globals():
        print ( f"[testAnalysisCombo] did not find {name}" )
    try:
        func = globals()[name]
        setup = func()
        return addDefaults ( setup )
    except KeyError as e:
        print ( f"[testAnalysisCombo] {name} not found: {e}" )
        listSetups()
        sys.exit()

def listSetups( printOut = True ):
    """ list all the setups,
    :param printOut: if true, then print to stdout
    :returns: list of setups
    """
    g = globals()
    ret = []
    if printOut:
        print ( "Available setups:" )
    for i,f in g.items():
        if i.startswith ( "getSetup" ) and not i == "getSetup":
            l = i.replace("getSetup","" )
            ret.append ( l )
            if hasattr ( f, "__doc__" ):
                docstring = f.__doc__
                l+= f" {docstring}"
            if printOut:
                print ( f" - {l}" )
    return ret

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser( description = "plot likelihoods" )
    argparser.add_argument ( "-s", "--setup",
            help="choose setup (see --list for a list of options), or 'all' [TChiWZ09]",
            type=str, default="TChiWZ09" )
    argparser.add_argument ( "-l", "--list", action="store_true",
            help="list all setups" )
    argparser.add_argument ( "-R", "--dont_rewrite", action="store_true",
            help="do not rewrite dictionaries" )
    argparser.add_argument ( "-d", "--dbpath",
            help="database path [../../smodels-database]",
            type=str, default="../../smodels-database" )
    args = argparser.parse_args()
    dbpath[0] = args.dbpath
    if args.list:
       listSetups()
       sys.exit()
    if args.setup == "all":
        ret = listSetups( printOut = False )
        for r in ret:
            setup = getSetup ( r )
            if args.dont_rewrite:
                setup["rewrite"]=False
            print ( f"[testAnalysisCombo] now testing {r}" )
            testAnalysisCombo( setup )
        sys.exit()

    setup = getSetup( args.setup )
    if args.dont_rewrite:
        setup["rewrite"]=False
    testAnalysisCombo( setup )

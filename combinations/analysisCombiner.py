""" Code that decides which analyses can be combined and which cannot """

from smodels.theory.theoryPrediction import TheoryPrediction

def getExperimentName ( globI ):
    """ returns name of experiment of exp result """
    if "CMS" in globI.id:
        return "CMS"
    if "ATLAS" in globI.id:
        return "ATLAS"
    return "???"

def canCombine ( predA, predB, strategy="conservative" ):
    """ can we combine predA and predB? predA and predB can be
        individual predictions, or lists of predictions.
    :param strategy: combination strategy, can be conservative, moderate, aggressive
    """
    if type(predA) == list:
        for pA in predA:
            ret = canCombine ( pA, predB, strategy )
            if ret == False:
                return False
        return True
    if type(predB) == list:
        for pB in predB:
            ret = canCombine ( predA, pB, strategy )
            if ret == False:
                return False
        return True
    if type(predA)==TheoryPrediction:
        predA = predA.expResult.globalInfo
    if type(predB)==TheoryPrediction:
        predB = predB.expResult.globalInfo
    if strategy == "conservative":
        return canCombineConservative ( predA, predB )
    if strategy == "moderate":
        return canCombineModerate ( predA, predB )
    if strategy != "aggressive":
        print ( "Error: strategy ``%s'' unknown" % strategy )
        return None
    return canCombineAggressive ( predA, predB )

def canCombineModerate ( globA, globB ):
    """ method that defines what we allow to combine, moderate version.
         """
    if globA.sqrts != globB.sqrts:
        return True
    if getExperimentName(globA) != getExperimentName(globB):
        return True
    anaidA = globA.id
    anaidB = globB.id
    allowCombination = { "ATLAS-SUSY-2013-02": [ "ATLAS-SUSY-2013-11" ],
                         "CMS-SUS-13-012": [ "CMS-SUS-13-007" ] }
    if anaidA in allowCombination.keys():
        if anaidB in allowCombination[anaidA]:
            return True
    if anaidB in allowCombination.keys():
        if anaidA in allowCombination[anaidB]:
            return True
    return False

def canCombineAggressive ( globA, globB ):
    """ method that defines what we allow to combine, aggressive version.
         """
    if globA.sqrts != globB.sqrts:
        return True
    if getExperimentName(globA) != getExperimentName(globB):
        return True
    anaidA = globA.id
    anaidB = globB.id
    allowCombination = { "ATLAS-SUSY-2013-02": [ "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-11" ],
                         "CMS-SUS-13-012": [ "CMS-SUS-13-007", "CMS-SUS-13-013" ],
                         "CMS-SUS-12-024": [ "CMS-SUS-13-007", "CMS-SUS-13-013" ],
                         "CMS-SUS-13-007": [ "CMS-SUS-12-024", "CMS-SUS-13-012", "CMS-SUS-13-013" ],
                         "ATLAS-CONF-2013-024": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-037": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054" ],
                         "ATLAS-CONF-2013-047": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-048": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-053": [ "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ],
                         "ATLAS-CONF-2013-054": [ "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093" ] }
    if anaidA in allowCombination.keys():
        if anaidB in allowCombination[anaidA]:
            return True
    if anaidB in allowCombination.keys():
        if anaidA in allowCombination[anaidB]:
            return True
    return False

def canCombineConservative ( globA, globB ):
    """ method that defines what we allow to combine, conservative version.
         """
    if globA.sqrts != globB.sqrts:
        return True
    if getExperimentName(globA) != getExperimentName(globB):
        return True
    return False

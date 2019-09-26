#!/usr/bin/env python3

""" Code that decides which analyses can be combined and which cannot """

from smodels.theory.theoryPrediction import TheoryPrediction
import fnmatch

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
    elA, elB = None, None
    if type(predA)==TheoryPrediction:
        elA = predA.elements
        predA = predA.expResult.globalInfo
    if type(predB)==TheoryPrediction:
        elB = predB.elements
        predB = predB.expResult.globalInfo
    if strategy == "conservative":
        return canCombineConservative ( predA, predB, elA, elB )
    if strategy == "moderate":
        return canCombineModerate ( predA, predB, elA, elB )
    if strategy != "aggressive":
        print ( "Error: strategy ``%s'' unknown" % strategy )
        return None
    return canCombineAggressive ( predA, predB, elA, elB )

def canCombineModerate ( globA, globB, elA, elB ):
    """ method that defines what we allow to combine, moderate version.
         """
    if globA.sqrts != globB.sqrts:
        return True
    if getExperimentName(globA) != getExperimentName(globB):
        return True
    if hasOverlap ( elA, elB, globA, globB ):
        ## overlap in the constraints? then for sure a no!
        return False
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

def hasOverlap ( elA, elB, globA = None, globB = None ):
    """ is there an overlap in the elements in A and in B? """
    if elA is None or elB is None:
        return False
    for eA in elA:
        for eB in elB:
            # print ( "el %s is el %s? %s! %s!" % ( eA, eB, eA.__cmp__ ( eB ), eA == eB ) )
            if eA == eB: ## an element of elA is in elB
                return True
    return False

def canCombineAggressive ( globA, globB, elA, elB ):
    """ method that defines what we allow to combine, aggressive version.
         """
    if globA.sqrts != globB.sqrts:
        return True
    if getExperimentName(globA) != getExperimentName(globB):
        return True
    if hasOverlap ( elA, elB, globA, globB ):
        ## overlap in the constraints? then for sure a no!
        return False
    anaidA = globA.id
    anaidB = globB.id
    allowCombinationATLAS8TeV = { "ATLAS-SUSY-2013-02": [ "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-11" ],
              "ATLAS-CONF-2013-024": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-CONF-2013-037": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-19" ],
              "ATLAS-CONF-2013-047": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-CONF-2013-048": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-18", "ATLAS-SUSY-2013-23", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-18", "ATLAS-SUSY-2013-21", "ATLAS-SUSY-2014-03" ],
              "ATLAS-CONF-2013-053": [ "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15" ],
              "ATLAS-CONF-2013-054": [ "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23", "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-21" ],
              "ATLAS-SUSY-2013-02": [ "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-SUSY-2013-04": [ "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-SUSY-2013-09": [ "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-18", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-SUSY-2013-11": [ "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-18", "ATLAS-SUSY-2013-23" ],
              "ATLAS-SUSY-2013-12": [ "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-08", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-18", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23", "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089" ],
              "ATLAS-SUSY-2013-15": [ "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-19", "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089" ],
              "ATLAS-SUSY-2013-16": [ "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-SUSY-2013-18": [ "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23" ],
              "ATLAS-SUSY-2014-03": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-21" ],
              "ATLAS-SUSY-2013-21": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15" ],
              "ATLAS-SUSY-2013-18": [ "ATLAS-CONF-2013-048", "ATLAS-SUSY-2013-11" ],
              "ATLAS-SUSY-2013-16": [ "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15" ],
              "ATLAS-SUSY-2013-15": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-21", "ATLAS-SUSY-2014-03" ],
              "ATLAS-SUSY-2013-11": [ "ATLAS-CONF-2013-024", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-047", "ATLAS-CONF-2013-053", "ATLAS-CONF-2013-054", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-02", "ATLAS-SUSY-2013-04", "ATLAS-SUSY-2013-05", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-16", "ATLAS-SUSY-2013-18", "ATLAS-SUSY-2013-21", "ATLAS-SUSY-2014-03" ],
              "ATLAS-SUSY-2013-05": [ "ATLAS-CONF-2013-007", "ATLAS-CONF-2013-089", "ATLAS-SUSY-2013-09", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-12", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-19", "ATLAS-SUSY-2013-23", "ATLAS-CONF-2013-037", "ATLAS-CONF-2013-048", "ATLAS-CONF-2013-062", "ATLAS-CONF-2013-093", "ATLAS-SUSY-2013-11", "ATLAS-SUSY-2013-15", "ATLAS-SUSY-2013-21" ],
              "ATLAS-CONF-2013-061": [ "ATLAS-SUSY-2013-21", ] ,

    }
    allowCombinationCMS8TeV = {
                         "CMS-SUS-13-012": [ "CMS-SUS-13-007", "CMS-SUS-13-013" ],
                         "CMS-SUS-12-024": [ "CMS-SUS-13-007", "CMS-SUS-13-013" ],
                         "CMS-SUS-13-007": [ "CMS-SUS-12-024", "CMS-SUS-13-012", "CMS-SUS-13-013", "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-PAS-SUS-13-018", "CMS-PAS-SUS-13-023" ],
                         "CMS-SUS-13-002": [ "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-PAS-SUS-13-018", "CMS-PAS-SUS-13-023", "CMS-SUS-12-024", "CMS-SUS-12-028", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-012", "CMS-SUS-13-013", "CMS-SUS-13-019", "CMS-SUS-14-021" ],
                         "CMS-SUS-14-021": [ "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-013" ],
                         "CMS-SUS-14-010": [ "CMS-EXO-12-026" ],
                         "CMS-SUS-13-013": [ "CMS-PAS-SUS-13-016", "CMS-EXO-12-026", "CMS-PAS-SUS-13-018", "CMS-PAS-SUS-13-023", "CMS-SUS-12-024", "CMS-SUS-12-028", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-012", "CMS-SUS-13-019", "CMS-SUS-14-021" ],
                         "CMS-SUS-13-012": [ "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-013" ],
                         "CMS-SUS-12-028": [ "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-013" ],
                         "CMS-SUS-12-024": [ "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-013" ],
                         "CMS-PAS-SUS-13-016": [ "CMS-SUS-13-013", "CMS-EXO-12-026", "CMS-PAS-SUS-13-018", "CMS-PAS-SUS-13-023", "CMS-SUS-12-024", "CMS-SUS-12-028", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-012", "CMS-SUS-13-019", "CMS-SUS-14-021" ],
                         "CMS-SUS-13-015": [ "CMS-EXO-12-026", "CMS-PAS-SUS-13-016", "CMS-SUS-13-002", "CMS-SUS-13-007", "CMS-SUS-13-011", "CMS-SUS-13-013" ],
                         "CMS-EXO-13-006": [ "CMS-SUS-*", "CMS-PAS-SUS-*" ],
                         "CMS-EXO-12-026": [ "CMS-SUS-*", "CMS-PAS-SUS-*" ],
    }

    allowCombinationCMS13TeV = {
        "CMS-PAS-EXO-16-036": [ "CMS-PAS-SUS-*", "CMS-SUS-*" ],
        "CMS-PAS-SUS-16-022": [ "CMS-PAS-EXO-16-036", "CMS-PAS-SUS-16-052", "CMS-SUS-16-032", "CMS-SUS-16-033", "CMS-SUS-16-034", "CMS-SUS-16-035", "CMS-SUS-16-036", "CMS-SUS-16-037", "CMS-SUS-16-042", "CMS-SUS-16-045", "CMS-SUS-16-046", "CMS-SUS-16-047", "CMS-SUS-16-049", "CMS-SUS-16-050", "CMS-SUS-16-051", "CMS-SUS-17-001" ],
        "CMS-SUS-16-051": [ "CMS-PAS-EXO-16-036", "CMS-PAS-SUS-16-022", "CMS-PAS-SUS-16-052", "CMS-PAS-SUS-17-004", "CMS-SUS-16-032", "CMS-SUS-16-033", "CMS-SUS-16-034", "CMS-SUS-16-035", "CMS-SUS-16-036", "CMS-SUS-16-039", "CMS-SUS-16-041", "CMS-SUS-16-045", "CMS-SUS-16-046", "CMS-SUS-16-047", "CMS-SUS-16-049", "CMS-SUS-16-050", "CMS-SUS-17-001", "CMS-PAS-SUS-16-052-agg" ],
        "CMS-SUS-16-050": [ "CMS-PAS-EXO-16-036", "CMS-PAS-SUS-16-022", "CMS-PAS-SUS-17-004", "CMS-SUS-16-034", "CMS-SUS-16-035", "CMS-SUS-16-037", "CMS-SUS-16-039", "CMS-SUS-16-041", "CMS-SUS-16-042", "CMS-SUS-16-051" ],
        "CMS-SUS-16-049": [ "CMS-PAS-EXO-16-036", "CMS-PAS-SUS-16-022", "CMS-PAS-SUS-17-004", "CMS-SUS-16-034", "CMS-SUS-16-035", "CMS-SUS-16-037", "CMS-SUS-16-039", "CMS-SUS-16-041", "CMS-SUS-16-042", "CMS-SUS-16-051" ],
        "CMS-SUS-16-036": [ "CMS-PAS-EXO-16-036", "CMS-PAS-SUS-16-022", "CMS-PAS-SUS-17-004", "CMS-SUS-16-034", "CMS-SUS-16-035", "CMS-SUS-16-037", "CMS-SUS-16-039", "CMS-SUS-16-041", "CMS-SUS-16-042", "CMS-SUS-16-051" ],
    }
    allowCombinationATLAS13TeV = {
        "ATLAS-SUSY-2015-01": [ "ATLAS-SUSY-2015-02", "ATLAS-SUSY-2015-09", "ATLAS-SUSY-2016-14", "ATLAS-SUSY-2016-17", "ATLAS-SUSY-2016-33", "ATLAS-SUSY-2017-03", "ATLAS-SUSY-2015-02" ],
        "ATLAS-SUSY-2015-02": [ "ATLAS-SUSY-2015-01", "ATLAS-SUSY-2015-09", "ATLAS-SUSY-2016-14", "ATLAS-SUSY-2016-17", "ATLAS-SUSY-2016-26", "ATLAS-SUSY-2016-33", "ATLAS-SUSY-2017-03", "ATLAS-SUSY-2015-06", "ATLAS-SUSY-2016-07" ],
        "ATLAS-SUSY-2015-09": [ "ATLAS-SUSY-2015-01", "ATLAS-SUSY-2015-02", "ATLAS-SUSY-2016-26", "ATLAS-SUSY-2015-02", "ATLAS-SUSY-2015-06", "ATLAS-SUSY-2016-07" ],
        "ATLAS-SUSY-2016-08": [ ],
        "ATLAS-SUSY-2016-07": [ "ATLAS-SUSY-2015-02", "ATLAS-SUSY-2015-09", "ATLAS-SUSY-2016-14", "ATLAS-SUSY-2016-17", "ATLAS-SUSY-2016-33", "ATLAS-SUSY-2017-03", "ATLAS-SUSY-2015-02" ],
        "ATLAS-SUSY-2015-06": [ "ATLAS-SUSY-2015-02", "ATLAS-SUSY-2015-09", "ATLAS-SUSY-2016-14", "ATLAS-SUSY-2016-17", "ATLAS-SUSY-2016-33", "ATLAS-SUSY-2017-03", "ATLAS-SUSY-2015-02" ],
    }
    allowCombination = {}
    allowCombination.update ( allowCombinationATLAS8TeV )
    allowCombination.update ( allowCombinationCMS8TeV )
    allowCombination.update ( allowCombinationATLAS13TeV )
    allowCombination.update ( allowCombinationCMS13TeV )
    if anaidA in allowCombination.keys():
        for i in allowCombination[anaidA]:
            if len ( fnmatch.filter ( [anaidB ], i ) ) == 1:
                return True
    if anaidB in allowCombination.keys():
        for i in allowCombination[anaidB]:
            if len ( fnmatch.filter ( [anaidA ], i ) ) == 1:
                return True
        if anaidA in allowCombination[anaidB]:
            return True
    return False

def canCombineConservative ( globA, globB, elA, elB ):
    """ method that defines what we allow to combine, conservative version.
         """
    if globA.sqrts != globB.sqrts:
        return True
    if getExperimentName(globA) != getExperimentName(globB):
        return True
    return False

if __name__ == "__main__":
    from smodels.experiment.databaseObj import Database
    db = Database ( "official" )
    results = db.getExpResults()
    strategy="aggressive"
    ctr,combinable=0,0
    for x,e in enumerate(results):
        for y,f in enumerate(results):
            if y <= x:
                continue
            ctr += 1
            isUn = canCombine ( e.globalInfo, f.globalInfo, strategy )
            combinable+=isUn
    print ( "Can combine %d/%d results" % ( combinable, ctr ) )

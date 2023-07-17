
# coding: utf-8

# ### How to run Fastlim on a list of SLHA files

# In[1]:

"""setup - Import some smodels tools to deal with fastlim"""
import sys,os
sys.path.append('../fastlim_tools/runTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from smodels.base.physicsUnits import fb
from gridFastlim import runFastlimFor
from fastlimOutput import equalObjs
import glob
from collections import OrderedDict
import unittest

class testRunFastlimG(unittest.TestCase):
    
    def test(self):

        slhaDir = os.path.join(os.getcwd(),'slhaFiles/')
        fastlimdir = os.path.join(os.getcwd(),'../fastlim_tools/fastlim-1.0/')
        #Runs Fastlim on slhaDir to generate the output as .sms files
        result = runFastlimFor(slhaDir,fastlimdir,expResID=None,txname=None)
        print 'Files generated:\n',result
        
        
        # In[ ]:
        
        """Check if the correct number of files was produced"""
        assert len(result) == len(glob.glob(slhaDir+"*.slha"))
        
        
        # ##### Verify the output
        
        # In[2]:
        
        """setup - Define default output"""
        slhaDir = os.path.join(os.getcwd(),'slhaFiles/')
        expectedRes ={'1a7crtfzX1SKEXI.sms': {'ExptRes': [{'maxcond': 0.0, 'tval': 0.0042243902439, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.175609756098, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-024','expectedBG': 4.7 , 'DataSet': 'SR2:MET>300' , 'ObservedN': 2},
                                                        {'maxcond': 0.0, 'tval': 0.0003596059113300493, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 1.1330049261083743, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-054','expectedBG': 40.0 , 'DataSet': '8j50flavor1b-jets' , 'ObservedN': 44},
                                                        {'maxcond': 0.0, 'tval': 0.10407960199, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.4477611940, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-053','expectedBG': 15.8 , 'DataSet': 'SRAmCT250' , 'ObservedN': 14},
                                                        {'maxcond': 0.0, 'tval': 0.00013043478260869567, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.4106280193236715, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-037','expectedBG': 5.0 , 'DataSet': 'SRtN3' , 'ObservedN': 7},
                                                        {'maxcond': 0.0, 'tval': 3.4482758620689657e-05, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.22999999999999998, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-048','expectedBG': 4.3 , 'DataSet': 'SRM120' , 'ObservedN': 3},
                                                        {'maxcond': 0.0, 'tval': 5.41871921182266e-05, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.29556650246305416, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-062','expectedBG': 3.9 , 'DataSet': 'incHL3j_e' , 'ObservedN': 4},
                                                        {'maxcond': 0.0, 'tval': 0.00364676616915, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.228855721, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-061','expectedBG': 3.0 , 'DataSet': 'SR-0l-4j-A' , 'ObservedN': 2},
                                                        {'maxcond': 0.0, 'tval': 0.10239901477832512, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 4.0, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-047','expectedBG': 210.0 , 'DataSet': 'CMedium' , 'ObservedN': 228},
                                                        {'maxcond': 0.0, 'tval': 4.926108374384236e-06, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.21674876847290642, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-093','expectedBG': 2.1 , 'DataSet': 'SRBh' , 'ObservedN': 2}],                 'sbotmix': {'SB21': -0.999853136, 'SB11': 0.0171378385, 'SB12': 0.999853136, 'SB22': 0.0171378385},
                 'mass': OrderedDict([(24, 80.4182464), (25, 124.066542), (35, 1999.34508), (36, 2000.00002),
                                      (37, 2001.68498), (5, 4.85697885), (1000001, 3526.32489), (2000001, 3521.01173),
                                      (1000002, 3525.59921), (2000002, 3521.62673), (1000003, 3526.32489),
                                      (2000003, 3521.01173), (1000004, 3525.59921), (2000004, 3521.62673),
                                      (1000005, 660.353167), (2000005, 1328.76453), (1000006, 935.060852),
                                      (2000006, 1431.8675), (1000011, 5009.34603), (2000011, 5004.14816),
                                      (1000012, 5008.40821), (1000013, 5009.34603), (2000013, 5004.14816),
                                      (1000014, 5008.40821), (1000015, 5006.6248), (2000015, 5011.76896),
                                      (1000016, 5010.03273), (1000021, 2332.49912), (1000022, 368.872682),
                                      (1000023, 545.697927), (1000025, -555.385523), (1000035, 794.486146),
                                      (1000024, 541.491105), (1000037, 794.506655)]),
                 'chamix': {'V22': -0.274681728, 'V21': -0.961535204, 'V12': 0.961535204, 'V11': -0.274681728,
                            'U21': -0.980378433, 'U22': -0.197124653, 'U11': -0.197124653, 'U12': 0.980378433},
                 'extra': {'sigmacut': 0.0, 'tool' : 'fastlim'}, 'MM': {}, 'MINPAR': {3: 19.624},
                           'EXTPAR': {0: -1.0, 1: 370.0, 2: 740.0, 3: 2220.0, 11: 3341.5, 12: -440.39, 13: 0.0,
                                      23: 547.0, 26: 2000.0, 31: 5000.0, 32: 5000.0, 33: 5000.0, 34: 5000.0,
                                      35: 5000.0, 36: 5000.0, 41: 3506.7, 42: 3506.7, 43: 1349.1, 44: 3506.7,
                                      45: 3506.7, 46: 1110.0, 47: 3506.7, 48: 3506.7, 49: 662.73},
                 'stopmix': {'ST22': -0.481296834, 'ST21': -0.876557675, 'ST12': 0.876557675, 'ST11': -0.481296834},
                 'chimix': {'N12': -0.0213401336, 'N13': 0.152484503, 'N11': 0.982386309, 'N14': -0.1058783}},
        
                      
        '1A3jht421zAtzR2.sms' : {'ExptRes': [{'maxcond': 0.0, 'tval': 0.00601463414634, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.175609756098, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-024','expectedBG': 4.7 , 'DataSet': 'SR2:MET>300' , 'ObservedN': 2},
                                            {'maxcond': 0.0, 'tval': 0.000665024630542, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.19704433, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-054','expectedBG': 3.2 , 'DataSet': '10j50MJ340' , 'ObservedN': 1},
                                            {'maxcond': 0.0, 'tval': 0.0003980099502487562, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.4477611940298507, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-053','expectedBG': 15.8 , 'DataSet': 'SRAmCT250' , 'ObservedN': 14},
                                            {'maxcond': 0.0, 'tval': 0.00671980676329, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.410628019, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-037','expectedBG': 5.0 , 'DataSet': 'SRtN3' , 'ObservedN': 7},
                                            {'maxcond': 0.0, 'tval': 2.46305418719e-05, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.51, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-049','expectedBG': 20.7 , 'DataSet': 'em:mT2>90' , 'ObservedN': 19},
                                            {'maxcond': 0.0, 'tval': 0.0017881773399, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.22999999, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-048','expectedBG': 4.3 , 'DataSet': 'SRM120' , 'ObservedN': 3},
                                            {'maxcond': 0.0, 'tval': 0.0015123152709359607, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.14778325123152708, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-062','expectedBG': 1.7 , 'DataSet': 'incHL6j_m' , 'ObservedN': 0},
                                            {'maxcond': 0.0, 'tval': 0.00198009950249, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.14925373, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-061','expectedBG': 7.4 , 'DataSet': 'SR-1l-6j-B' , 'ObservedN': 0},
                                            {'maxcond': 0.0, 'tval': 0.00112315270936, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.11822660, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-047','expectedBG': 1.6 , 'DataSet': 'CTight' , 'ObservedN': 0},
                                            {'maxcond': 0.0, 'tval': 0.00022660098522167486, 'AnalysisTopo': [], 'DaughterMass': 0.0, 'exptlimit': 0.21674876847290642, 'MotherMass': 0.0, 'AnalysisSqrts': 8, 'AnalysisName': 'ATLAS-CONF-2013-093','expectedBG': 2.1 , 'DataSet': 'SRBh' , 'ObservedN': 2}],                                  'sbotmix': {'SB21': -0.00260652805, 'SB11': 0.999996603, 'SB12': 0.00260652805, 
                                             'SB22': 0.999996603}, 
                                 'mass': OrderedDict([(24, 80.42463), (25, 127.331753), (35, 2000.18898), 
                                                      (36, 1999.99997), (37, 2001.93345), (5, 4.85697885), 
                                                      (1000001, 4000.81913), (2000001, 3994.3546), (1000002, 4000.17072), 
                                                      (2000002, 3995.12005), (1000003, 4000.81913), (2000003, 3994.3546), 
                                                      (1000004, 4000.17072), (2000004, 3995.12005), (1000005, 1201.55776), 
                                                      (2000005, 1940.03024), (1000006, 641.528157), (2000006, 1248.15667), 
                                                      (1000011, 5009.84755), (2000011, 5004.19262), (1000012, 5008.89918), 
                                                      (1000013, 5009.84755), (2000013, 5004.19262), (1000014, 5008.89918),
                                                      (1000015, 5006.78316), (2000015, 5011.20891), (1000016, 5010.21326), 
                                                      (1000021, 1386.55643), (1000022, 133.896343), (1000023, -164.585195),
                                                      (1000025, 224.126077), (1000035, 456.565911), (1000024, 151.029718),
                                                      (1000037, 456.54511)]), 
                                 'chamix': {'V22': -0.284922952, 'V21': -0.958550422, 'V12': 0.958550422, 
                                            'V11': -0.284922952, 'U21': -0.993370629, 'U22': -0.114955615, 
                                            'U11': -0.114955615, 'U12': 0.993370629}, 
                                 'extra': {'sigmacut': 0.0, 'tool' : 'fastlim'}, 'MM': {}, 'MINPAR': {3: 14.413}, 
                                             'EXTPAR': {0: -1.0, 1: 205.54, 2: 411.08, 3: 1233.2, 11: 2108.8, 
                                                        12: -444.75, 13: 0.0, 23: 155.46, 26: 2000.0, 31: 5000.0, 
                                                        32: 5000.0, 33: 5000.0, 34: 5000.0, 35: 5000.0, 36: 5000.0, 
                                                        41: 3970.2, 42: 3970.2, 43: 1190.8, 44: 3970.2, 45: 3970.2, 
                                                        46: 690.05, 47: 3970.2, 48: 3970.2, 49: 1923.3}, 
                                 'stopmix': {'ST22': -0.293155177, 'ST21': -0.956064873, 'ST12': 0.956064873,
                                             'ST11': -0.293155177}, 
                                 'chimix': {'N12': -0.166629898, 'N13': 0.68743101, 'N11': 0.382484751, 
                                            'N14': -0.594456474}}}
        
        
        # In[3]:
        
        """Check the output"""
        for fname,defaultDict in expectedRes.items():
            f = open(slhaDir + fname,'r')
            resDict = eval(f.read())
            f.close()
            os.remove(slhaDir + fname)
            assert equalObjs(defaultDict,resDict,0.01) == True



# In[ ]:

if __name__ == "__main__":
    unittest.main()


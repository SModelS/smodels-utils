#FIXME maybe better to use objects rather than dictionaries?
#FIXME there should be some way to generate this automatically reading MA5/CM files
#FIXME change MA5_SR_Name to SR_Name


import os

MA5_Analyses_Dicts = [
{'Name'        : 'cms_sus_14_001_TopTag' ,
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'MET200-350__Nbjets=1' ,          'Official_SR_Name' : 'Official_region1' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MET>350__Nbjets=1' ,             'Official_SR_Name' : 'Official_region2' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },              
                    { 'MA5_SR_Name' : 'MET200-350__Nbjets>1' ,          'Official_SR_Name' : 'Official_region3' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MET>350__Nbjets>1' ,             'Official_SR_Name' : 'Official_region4' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 }
               ]
},

{'Name'        : 'atlas_susy_2013_21' ,
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'M1' ,                           'Official_SR_Name' : 'Official_region1' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'M2' ,                           'Official_SR_Name' : 'Official_region2' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },               
                    { 'MA5_SR_Name' : 'M3' ,                           'Official_SR_Name' : 'Official_region3' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
               ]
},

{'Name'        : 'cms_sus_13_016' ,
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'Gluino_to_TT_neutralino' ,      'Official_SR_Name' : 'Official_region1' , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
               ]
},


# TODO the above numbers are not real, only the ones for these following two analyses are correct


{'Name'        : 'atlas_sus_13_05' ,
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 150' ,      'Official_SR_Name' : 'SRA-mCT150' , 'Obs': 102 , 'Bkg': 94 ,   'Err': 13 },
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 200' ,      'Official_SR_Name' : 'SRA-mCT200' , 'Obs': 48  , 'Bkg': 39 ,   'Err': 6 },
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 250' ,      'Official_SR_Name' : 'SRA-mCT250' , 'Obs': 14  , 'Bkg': 15.8 , 'Err': 2.8 }, 
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 300' ,      'Official_SR_Name' : 'SRA-mCT300' , 'Obs': 7   , 'Bkg': 5.9 ,  'Err': 1.1 }, 
                    { 'MA5_SR_Name' : 'SRA, HighDeltaM, MET > 150, MCT > 350' ,      'Official_SR_Name' : 'SRA-mCT350' , 'Obs': 3   , 'Bkg': 2.5  , 'Err': 0.6 }, 
                    { 'MA5_SR_Name' : 'SRB, LowDeltaM, MET > 250'             ,      'Official_SR_Name' : 'SRB'         , 'Obs': 65  , 'Bkg': 64   , 'Err': 10 }, 

               ]
},

{'Name'        : 'atlas_susy_2013_11' ,
 'SR_Dict_List' : [ { 'MA5_SR_Name' : 'MT2-90 ee;MT2-90 mumu' ,         'Official_SR_Name' : 'mT2-90-SF'      , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-90 emu' ,                    'Official_SR_Name' : 'mT2-90-DF'      , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-120 ee;MT2-120 mumu' ,       'Official_SR_Name' : 'mT2-120-SF'    , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-120 emu' ,                   'Official_SR_Name' : 'mT2-120-DF'    , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-150 ee;MT2-150 mumu' ,       'Official_SR_Name' : 'mT2-150-SF'    , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'MT2-150 emu' ,                   'Official_SR_Name' : 'mT2-150-DF'     , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWa ee;WWa mumu' ,               'Official_SR_Name' : 'WWa-SF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWa emu' ,                       'Official_SR_Name' : 'WWa-DF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWb ee;WWb mumu' ,               'Official_SR_Name' : 'WWb-SF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWb emu' ,                       'Official_SR_Name' : 'WWb-DF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWc ee;WWc mumu' ,               'Official_SR_Name' : 'WWc-SF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'WWc emu' ,                       'Official_SR_Name' : 'WWc-DF'         , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 },
                    { 'MA5_SR_Name' : 'Zjets ee;Zjets mumu' ,           'Official_SR_Name' : 'Zjets'          , 'Obs': 10 , 'Bkg': 9 , 'Err': 3 }

                   ]
                      },

]

CM_Analyses_Dicts= []
def get_CM_Analyses_Dict(cm_data_dir=''):
    if not cm_data_dir or not os.path.isdir(cm_data_dir):
        print "CheckMATE data directory %s not found!" %cm_data_dir
        return None
    ret = []
    for f in os.listdir(cm_data_dir):
        if not "ref.dat" in f: continue
        dicEntry = {}
        ana = f.split("_ref")[0]
        dicEntry["Name"] = ana
        dicEntry['SR_Dict_List']=[]
        getEntry = []
        for l in open(os.path.join(cm_data_dir,f)):
            dictSR = {}
            l = l.strip().split()
            if len(getEntry)==0:
                getEntry.append(l.index("SR"))
                getEntry.append(l.index("obs"))
                getEntry.append(l.index("bkg"))
                if "bkg_err" in l:
                    getEntry.append(l.index("bkg_err"))
                else: getEntry.append(None) #FIXME non standard error definition, dont know what to do for now
            dictSR['SR_Name'] = l[getEntry[0]]
            dictSR['Official_SR_Name'] = l[getEntry[0]] #NOTE this is a dummy, we dont have the official name
            dictSR['Obs'] = int(l[getEntry[1]])
            dictSR['Bkg'] = float(l[getEntry[2]])
            if getEntry[3]: dictSR['Err'] = float(l[getEntry[3]])
            else: dictSR['Err'] = None
            dicEntry['SR_Dict_List'].append(dictSR)
        ret.append(dicEntry)
    return ret


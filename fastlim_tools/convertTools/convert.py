#!/usr/bin/env python

"""
.. module:: convert
   :synopsis: used to create info.txt, txname.txt, twiki.txt and sms.py.

.. moduleauthor: Wolfgang Waltenberger

"""
import sys
import os
import argparse
import types

argparser = argparse.ArgumentParser(description = \
'create info.txt, txname.txt, twiki.txt and sms.py')
argparser.add_argument ('-utilsPath', '--utilsPath', \
help = 'path to the package smodels_utils',\
type = types.StringType)
args = argparser.parse_args()

if args.utilsPath:
    utilsPath = args.utilsPath
else:
    databaseRoot = '../../../../'
    sys.path.append(os.path.abspath(databaseRoot))
    from utilsPath import utilsPath
    utilsPath = databaseRoot + utilsPath

sys.path.append(os.path.abspath(utilsPath))
from smodels_utils.dataPreparation.inputObjects import TxNameInput, MetaInfoInput
from smodels_utils.dataPreparation.databaseCreation import databaseCreator
from smodels_utils.dataPreparation.origPlotObjects import x, y, z


#+++++++ global info block ++++++++++++++

import os, glob
dir=os.getcwd()
## print dir
pos1=dir.find("ATLAS/")+6
pos=dir.rfind("/data")
expid = dir[pos1:pos]
print "[convert.py] expid=",expid
signalregion=dir[pos+1:]
print "[convert.py] signalregion=",signalregion

info = MetaInfoInput(expid)
info.signalRegion = signalregion
info.url ='https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/%s/' % expid
info.sqrts = 8
info.prettyName = ''
info.private = True
info.arxiv = ''
info.contact ='fastlim'
info.publication = ''
info.lumi = 1.0
info.comment = 'created from fastlim-1.0'
info.supersededBy = ''
info.implementedBy = ''
 
def getConstraints ( txname, analysis ):
    constraints =  { "T2tt": "[[['t+']],[['t-']]]", "T2bb": "[[['b']],[['b']]]",
                     "T2": "[[['jet']],[['jet']]]",
                     "T2gg": "[[['jet']],[['jet']]]",
                     "T2bt": "[[['b']],[['t']]]", 
                     "T1tttt": "[[['t+','t-']],[['t+','t-']]]",
                     "T5tttt": "[[['t+'],['t-']],[['t+'],['t-']]]+" \
                               "[[['t-'],['t+']],[['t-'],['t+']]]",
                     "T5bbbb": "[[['b'],['b']],[['b'],['b']]]",
                     "T5bbbt": "[[['b'],['b']],[['b'],['t']]]",
                     "T1bbtt": "[[['b','b']],[['t+','t-']]]", 
                     "T1btbt": "[[['b','t']],[['b','t']]]",
                     "T1bbqq": "[[['b','b']],[['jet','jet']]]", 
                     "T1bbbb": "[[['b','b']],[['b','b']]]",
                     "T1bbbt": "[[['b','b']],[['b','t']]]", 
                     "T5btbt": "[[['b'],['t']],[['b'],['t']]]",
                     "T5tbtb": "[[['t'],['b']],[['t'],['b']]]", 
                     "T5tbtt": "[[['t'],['b']],[['t+'],['t-']]]+[[['t'],['b']],[['t-'],['t+']]]",
                     "TGQqtt": "[[['jet']],[['t+','t-']]]", 
                     "TGQ": "[[['jet']],[['jet','jet']]]",
                     "TGQbtq": "[[['b','t']],[['jet']]]", 
                     "TGQbbq": "[[['b','b']],[['jet']]]",
                     "T1btqq": "[[['b','t']],[['jet','jet']]]", 
                     "T1qqtt": "[[['jet','jet']],[['t+','t-']]]",
                     "T1bttt": "[[['b','t']],[['t+','t-']]]", 
                     "T1": "[[['jet','jet']],[['jet','jet']]]" }
    if txname == "T2tt": 
        tmp = expid.replace ( "ATLAS-CONF-","" ).replace("-eff","" )
        if tmp in [ "2013-024", "2013-037", "2013-047", "2013-053", "2013-054",
                      "2013-061", "2013-062", "2013-093" ]:
            return "[[['t']],[['t']]]"
    return constraints[txname]

figure={}
figure["T1"]='fig_07a.pdf'

figureUrl={}
figureUrl["T1"]='https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/ATLAS-CONF-2013-047/fig_07a.pdf'

for i in os.listdir("orig/"):
    # print("[convert.py] i=%s" % i)
    if i[-5:]!=".effi": continue
    txname=i[:-5]
    print "[convert.py] Txname: %s" % txname
    if txname in [ ]: ## "T2gg" ]:
        print "[convert.py] Skipping Txname: %s. Dont know how to handle." % txname
        continue
    tmp= TxNameInput ( txname )
    tmp.on.constraint = getConstraints(txname,expid)
    # sys.exit()
    tmp.on.conditionDescription=None
    tmp.on.condition = None
    if i[:2] in [ "T5", "T6" ]:
        ## print("[convert.py] tmp=%s" % type(tmp))
        tmp_1 = tmp.addMassPlane ( motherMass = x, lspMass=z, interMass0= y )
        tmp_1.efficiencyMap3D.setSource ( './orig/%s.effi' % txname, 'effi', objectName = None, index = None )
        ## print("[type] %s" % type ( tmp_1 ) )
#        continue
    else:
        if txname=="TGQ":
            tmp_1 = tmp.addMassPlane (motherMass = x , lspMass = y )
#            tmp_1.setBranch_1 ( x, lspMass = y )
#            tmp_1.setBranch_2 ( x, lspMass = y )
        else:
            tmp_1 = tmp.addMassPlane (motherMass = x , lspMass = y )
        tmp_1.efficiencyMap.setSource( './orig/%s.effi' % txname, 'effi', objectName = None, index = None )
    if os.path.exists ( './orig/%s_excl.dat' % txname ):
        tmp_1.obsExclusion.setSource( './orig/%s_excl.dat' % txname, 'txt', objectName = None, index = None )
    if txname in figure:
        tmp_1.figure = figure[txname]
    if txname in figureUrl:
        tmp_1.figureUrl = figureUrl[txname]

def translate ( filename ):
    ff=open(filename)
    lines=ff.readlines()[3:]
    ff.close()
    newfilename=filename.replace("./orig/","").replace(".effi",".hlp")
    w=open(newfilename,"w")
    for line in lines:
        a=line.split()
        f=[ float(a[0]), float(a[1]), float(a[2]), float(a[3]) ]
        line="[[[%.1f*GeV, %.1f*GeV, %.1f*GeV], [%.1f*GeV, %.1f*GeV, %.1f*GeV]], %f]," % \
              ( f[0], f[1], f[2], f[0], f[1], f[2], f[3] )
        w.write ( line +"\n" )
    w.close()

databaseCreator.infoFileDirectory="./"
databaseCreator.create( ask_for_name = False, create_dataInfo=False )

import os
os.unlink ("globalInfo.txt")

import glob
for i in glob.iglob ( "./validation/*" ):
    print "[convert.py] unlinking",i,"from",os.getcwd()
    os.unlink ( i )
os.rmdir ( "./validation" )
for i in glob.iglob ( "./sms.root" ):
    print "[convert.py] unlinking",i,"from",os.getcwd()
    os.unlink ( i )

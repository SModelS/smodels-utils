#!/usr/bin/env python

import sys

sys.path.append('../')


def main():
    from validation.validationObjs import ValidationPlot
    from validation.slhaCreator import TemplateFile
    from smodels.experiment.databaseObjects import ExpResult
    from smodels.experiment.infoObject import Info
    from smodels.experiment.databaseObjects import DataBase
    from smodels.tools.physicsUnits import GeV, fb, TeV, pb
    from smodels.experiment.databaseBrowser import Browser
    
    import logging
    from smodels.experiment.txnameObject import logger as ml
    ml.setLevel(level=logging.INFO)
    
    
    database = DataBase("/home/lessa/smodels-database/")
    expRes = database.getExpResults(analysisIDs=['ATLAS-CONF-2013-036'],
                                datasetIDs=[None],txnames=['TChiChiSlepSlep'])
    template = '../slha/templates/TChiChiSlepSlep.template'
    axes = '2*Eq(mother,x)_Eq(inter0,y)_Eq(lsp,x-80.0)'
    tempf = TemplateFile(template,axes)
    txnameObj = expRes.getTxNames()[0]  
    print tempf.checkFor(txnameObj, 500.,200.)
    sys.exit()
    
    browser = Browser(database)
    browser.loadExpResultsWith({'id' : ['CMS-SUS-13-004']})
    expRes = browser[0]
    txname = expRes.getTxnameWith({'txname': 'T1bbbb'})
    axes = txname.getInfo('axes')[0]
    valPlot = ValidationPlot(expRes,txname,axes)
    valPlot.setSLHAdir('/home/lessa/smodels-utils/slha/T1bbbb')
    valPlot.getData()
    valPlot.getPlot(silentMode=False)
    valPlot.savePlot()

if __name__ == "__main__":
    main()

#!/usr/bin/env python

import sys

sys.path.append('../')


def main():
    from andre_validation.validationObjs import ValidationPlot
    from smodels.experiment.databaseObjects import ExpResult
    from smodels.experiment.infoObject import Info
    from smodels.experiment.databaseObjects import DataBase
    from smodels.tools.physicsUnits import GeV, fb, TeV, pb
    from smodels.experiment.databaseBrowser import Browser
    
    import logging
    from smodels.experiment.txnameObject import logger as ml
    ml.setLevel(level=logging.INFO)
    
    
    database = DataBase("/home/lessa/smodels-database/")
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

#!/usr/bin/env python

"""
.. module:: checkTemplates
   :synopsis: Look for all Txnames in the database and check if the corresponding templates
              exist and have been properly defined

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys
sys.path.append('../../smodels/')
sys.path.append('../../smodels-utils/')

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
from smodels.experiment.databaseObjects import DataBase
from andre_validation.slhaCreator import TemplateFile


templateDir = '../slha/templates'

missTxnames = []
badTemplates = []
database = DataBase("/home/lessa/smodels-database/")
for expRes in database.expResultList:
    for txname in expRes.getTxNames():
        template = os.path.join(templateDir,txname.txname+'.template')
        if template in badTemplates: continue
        if txname.txname in missTxnames: continue
        #check if the txname.template file exists: 
        if not os.path.isfile(template):            
            missTxnames.append(txname.txname)
            print 'Template missing for %s' %txname.txname
        else:
            axes = txname.getInfo('axes')
            if not isinstance(axes,list): axes = [axes]
            for ax in axes:
                tempf = TemplateFile(template,ax)
                #Check if smodels produces the proper topologies/elements for a given set of masses:
                if not tempf.checkFor(txname, 500.,50.):
                    print 'Bad template in %s for \n %s' %(template,str(expRes))
                    badTemplates.append(template)
                 
print 'Missing TxNames:'                    
print missTxnames
              
print '\n\nBad Templates:'                    
print badTemplates
            
        
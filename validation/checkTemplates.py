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

from smodels.experiment.databaseObj import Database
from validation.slhaCreator import TemplateFile
from validation.slhaCreator import logger as vallogger
from smodels.tools.xsecComputer import logger as xseclogger

logger.setLevel(level=logging.WARNING)
vallogger.setLevel(level=logging.WARNING)
xseclogger.setLevel(level=logging.ERROR)


templateDir = '../slha/templates'

missTxnames = []
badTemplates = []
goodTemplates = []
errorTemplates = []
database = Database(os.path.expanduser("~/smodels-database/"))
for expRes in database.getExpResults(useNonValidated=True):
    #Skip efficiency-map analyses:
#     if 'efficiencyMap' in expRes.getValuesFor('dataType'): continue
    for txname in expRes.getTxNames():
#         if txname.txName != 'T5tbtb': continue
        #Skip incomplete analysis
        if txname.getMetaData('constraint') == 'not yet assigned': continue 
        template = os.path.join(templateDir,txname.txName+'.template')
        if template in goodTemplates: continue
        if template in badTemplates: continue
        if template in errorTemplates: continue
        if txname.txName in missTxnames: continue
        logger.info("Checking %s ..." %template)
        #check if the txname.template file exists: 
        if not os.path.isfile(template):            
            missTxnames.append(txname.txName)
            logger.warning('Template missing for %s' %txname.txName)
            continue
        try:
            axes = txname.getMetaData('axes')
            if not isinstance(axes,list): axes = [axes]
            for ax in axes:
                tempf = TemplateFile(template,ax)
                #Check if smodels produces the proper topologies/elements for a given set of masses:
                if not tempf.checkFor(txname,500.,300.,50.):
                    logger.error('Bad template in %s for \n %s' %(template,str(expRes)))
                    badTemplates.append(template)
                    break
            if not template in badTemplates:
                goodTemplates.append(template)
        except:
            errorTemplates.append(template)


                 
print '%i Missing TxNames:' %len(missTxnames)                    
print missTxnames
              
print '\n\n%i Bad Templates:' %len(badTemplates)    
print badTemplates

print '\n\n%i Error Templates:' %len(errorTemplates)               
print errorTemplates 
       
print '\n\n%i Good Templates:' %len(goodTemplates)              
print goodTemplates 
            
        

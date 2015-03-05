#!/usr/bin/env python

"""
.. module:: slhaCreator
   :synopsis: Main methods for generating SLHA files for a given Txname from a template

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
import tempfile


def createFile(axesDict,template,filename=None):
    """
    Creates a new SLHA file from the template.
    The entries on the template matching the axesDict labels/keys are replaced
    by the axesDict values.
    :param axesDict: dictionary with the axes definitions in string format (i.e. mother, lsp, inter0,...) as keys
                     and the corresponding mass as values in GeV (i.e. 300.)
    :param template: path to the template file. The template file must contain the axes labels where the
                     numerical values for the masses must appear.
    :param filename: filename for the new file. If None, a random name for the file will be generated,
                     with prefix template and suffix .slha
    :return: True if file has been successfully generated, False otherwise.
    """
    
    if not os.path.isfile(template):
        logger.error("Template file %s not found" %template)
        return False
    ftemplate = open(template,'r')    
    fdata = ftemplate.read()
    ftemplate.close()
    
    for ax in axesDict:
        if not ax in fdata:
            logger.error("Label %s not found in template file %s" %(ax,template))
            return False
        else:
            fdata = fdata.replace(ax,str(axesDict[ax]))
    
    if not filename:
        filename = tempfile.mkstemp(prefix=template[:template.rfind(".")]+"_",suffix=".slha")
        os.close(filename[0])
        filename = filename[1]
    newf = open(filename,'w')
    newf.write(fdata)
    newf.close()
    logger.info("File %s created." %filename)
    
    return True


if __name__ == "__main__":
    axesDict = {"mother" : 500., "lsp" : 200.}
    template = '/home/lessa/smodels-utils/slha/T2tt/T2tt_NLL.template'
    print createFile(axesDict,template)
    
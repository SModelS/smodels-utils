#!/usr/bin/env python3

"""
.. module:: validationHelpers
    :synopsis: various helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def getValidationFileContent ( validationfile : str ):
    """ get the content of the validation file, as a dictionary of 
        'data' and 'meta'
    :param validation file: filename
    :returns: dictionary with content of validation file
    """
    #Save data to file
    f = open( validationfile, 'r' )
    lines = f.readlines()
    f.close()
    nlines = len(lines)
    txt = "\n".join(lines[:-1])
    if nlines == 1:
        txt = "\n".join(lines[:])
    # print ( "txt", txt )
    ret = {}
    data = eval(txt.replace("validationData = ",""))
    ret["data"] = data
    meta = None
    if len(lines)>1 and lines[-1].startswith ( "meta" ):
        meta = eval(lines[-1].replace("meta = ",""))
    ret["meta"]=meta
    return ret

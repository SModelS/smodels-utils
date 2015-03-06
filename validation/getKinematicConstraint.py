#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds objects used by convert.py to create info.txt, sms.root, sms.py and newSms.py.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys, logging, os, ROOT
sys.path.insert(0,"../../")
sys.path.insert(0,"../../../")
sys.path.insert(0,"../")
from copy import deepcopy
from datetime import date


FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)

def _getKinConstraints( constraint ):
    
    """
    takes the on-shell constraint of a given txName,
    replace the SM-particles occurring in one Vertex 
    by the sum of their masses. 
    The masses of 'Z', 'W', 't' and 'h' are set 
    to: paricleMass - 2*decaywith
    The masses of all other SM-particles are set to 0
    
    :param txName: inputObjects.TxNameInput-object
    :raise missingOnConstraintError: if TxNameInput-object
    have no-shell constraint
    :raise constraintError: if on-shell constraint can not
    be interpreted as a list in the required format
    :return: list of lists, each list holds the mass-sum
    of the SM-particles for every vertex.
    or None if on-shell constraint set to:'not yet assigned'
    
    """
    
    massDict = {'Z': 86., 'W': 76.,'t': 169.,'h': 118}
    startString = '[[['
    endString = ']]]'
    kinConstraints = []
    txName="bla"
    if constraint == 'not yet assigned': return None
    if not isinstance(constraint, str):
        Errors().constraint(self.txName, constraint)
    if not endString in constraint or not startString in constraint:
        Errors().constraint(self.txName, constraint)
    for i in range(len(constraint)):
        if constraint[i:i + len(startString)] == startString:
            start = i
        if constraint[i:i + len(endString)] == endString:
            end = i + len(endString)
            kinConstraints.append(constraint[start:end])
    try:
        kinConstraints = \
        [eval(constraint) for constraint in kinConstraints]
    except:
        Errors().constraint(self.txName, constraint)
    for i, constraint in enumerate(kinConstraints):
        for j, branch  in enumerate(constraint):
            for k, vertex in enumerate(branch):
                massSum = 0.
                for particle in vertex:
                    particle = particle.replace('+','')
                    particle = particle.replace('-','')
                    if particle in massDict:
                        massSum = massSum + massDict[particle]
                kinConstraints[i][j][k] = massSum
    return kinConstraints
        

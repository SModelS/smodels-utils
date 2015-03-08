#!/usr/bin/env python

"""
.. module:: vertexChecking
   :synopsis: Holds The code to check the vertices for on- versus offshellness

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""   

import sys

class VertexChecker(object):
    
    """
    This class is designed to compute the off-shell
    vertices for a given mass array
    The on-shell constraints of txName are used to define 
    the SM-particles occurring in every vertex.
    The differences of the masses of the SUSY-particles related
    to one vertex are compared with the mass sum of the SM-particles
    in this vertex
    """

    def __init__(self, name, constraint ):
        
        """
        :param txNameObj: inputObjects.TxNameInput-object
        """
        
        self.txName = name
        self.kinConstraints = self._getKinConstraints(name,constraint)
        
        
    def getOffShellVertices(self, massArray):
        
        """
        compute the mass-difference between two adjacent
        masses in the mass array. Compare those mass differences
        with the masses held by self.kinConstraint. If the mass 
        difference is smaller then the assigned kinConstraint-mass
        the vertex is added to the list of off-shell vertices
        
        :param massArray: list containing two other lists. Each list contains 
        floats, representing the masses of the particles of each branch in GeV
        :raise decayChainError: if length of mass array not equal length of kinConstraint
        :return: list of off-shell vertices, each vertex is represented by a tuple 
        that contains two integers. The first one of those integers give the branch
        of the vertex and the second one the position of the vertex in the branch
        The count starts with 0. eg: (0,1) --> second vertex in first branch
        """

        offShellVertices = []
        massDeltaArray = [[],[]]
        for i, branch in enumerate(massArray):
            for j, mass in enumerate(branch):
                if j == 0: continue
                massDelta =branch[j-1] - mass
                massDeltaArray[i].append(massDelta)
                
        for kinConstraint in self.kinConstraints:
            for i, branch in enumerate(kinConstraint):
                # print "branch=",branch,"massDeltaArray=",massDeltaArray
                if len(branch) != len(massDeltaArray[i]):
                    Errors().decayChain(self.txName,\
                    len(branch),len(massDeltaArray[i]))
                for j, massDelta in enumerate(branch):
                    if massDeltaArray[i][j] <= massDelta:
                        if not (i,j) in offShellVertices:
                            offShellVertices.append((i,j))
        return offShellVertices
        
    def _getKinConstraints(self, name, constraint ):
        
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
        
    def __nonzero__(self):
        
        return bool(self.kinConstraints)
        
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def constraint(self, txName, constraint):
        
        m = self._starLine
        m = m + 'In VertexChecker: Error while reading the onshell constraint '
        m = m + 'for txName: %s\n' %txName
        m = m + "constraint have to be of form:\n"
        m = m + "\"[[['particle',...],...]][['particle',...],...]]\"\n"
        m = m + 'got: %s' %constraint
        m = m + self._starLine
        print(m)
        sys.exit()
        
    def decayChain(self, txName, constraintLen, massArrayLen):
        
        m = self._starLine
        m = m + 'In StandardLimits: Error while splitting upperlimits'
        m = m + 'for txName: %s\n' %txName
        m = m + "constraints and topology must have the same"
        m = m + "numbers of vertices\n"
        m = m + 'got:\n'
        m = m + 'vertices in constraint: %s\n' %constraintLen
        m = m + 'vertices in topology: %s' %massArrayLen
        m = m + self._starLine
        print(m)
        sys.exit()
        

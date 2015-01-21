#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds short objects used dataPreparation scripts.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""
import logging

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)  

class Locker(object):
    
    def __setattr__(self, name, attr):
        
        if name in self.allowedAttr:
            object.__setattr__(self, name, attr)
            return
        Errors().attr(name, type(self))
        
        
class ObjectList(list):
    
    def __init__(self, searchAttr, l = []):
    
        self.searchAttr = searchAttr
        list.__init__(self,l)
    
    def __getitem__(self, request):
        for obj in self:
            if getattr(obj, self.searchAttr) == request:
                return obj
        raise AttributeError
        
   
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def attr(self, name, attr):
    
        m = self._starLine
        m = m + '%s is not a allowed attripute ' %name 
        m = m + 'for %s\n'  %attr
        m = m + self._starLine
        print(m)
        sys.exit()
#!/usr/bin/env python

"""
.. module:: dataPreparation
   :synopsis: Holds short objects used dataPreparation scripts.

.. moduleauthor:: Michael Traub <michael.traub@gmx.at>

"""
import logging
import sys

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)  

class Locker(object):
    
    """Super-class to 'lock' a class.
    Every child-class of Locker needs 2 class-attributes:
    infoAttr: list of strings
    interAttr: list of strings
    Only attributes with names defined in one of those lists can
    be added to the child
    """
    
    
    def __setattr__(self, name, attr):
        
        """
        set a attripute if defiened in self.allowedAttr
        :param name: name of the attribute
        :param attr: value of the attribute
        :raise attrError: If name is not in self.allowedAttr
        """
        
        if name in self.allowedAttr:
            object.__setattr__(self, name, attr)
            return
        Errors().attr(name, type(self))
        
    @property
    def allowedAttr(self):
        
        """
        :return: list containing all entries of
        infoAttr and internalAttr
        """
        
        return self.infoAttr + self.internalAttr + self.requiredAttr
        
        
class ObjectList(list):
    
    """
    list-object with redefined __getitem__ methode
    An element of ObjectList can be addressed with 
    an user defined attribute (like the name of the element)
    instead with an index. The element need to have this 
    attribute
    """
    
    def __init__(self, searchAttr, l = []):
        
        """
        set the attribute for addressing the elements
        
        :param searchAttr: name of attribute used to address an element
        :param l: list of elements to be stored in the object
        """
    
        self.searchAttr = searchAttr
        list.__init__(self,l)
    
    def __getitem__(self, request):
        
        """
        :raise AttributeError: if no element with value of searchAttr == request 
        in ObjectList
        :return: first element with value of  serchAttr equals requested value
        """
        
        for obj in self:
            if getattr(obj, self.searchAttr) == request:
                return obj
        raise AttributeError
        
   
class Errors(object):
    
    def __init__(self):
        
        self._starLine = '\n************************************\n'
        
    def attr(self, name, attr):
    
        m = self._starLine
        m = m + '%s is not an allowed attribute ' %name 
        m = m + 'for %s\n'  %attr
        m = m + self._starLine
        print(m)
        sys.exit()

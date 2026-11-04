#!/usr/bin/env python3

"""
.. module:: modelInventor
   :synopsis: A class intended to "invent" models (slha files)

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
from pbase.constants import LSP, X2Z, X1W, X3Z, X2W

class ModelInventor:
  def __init__ ( self ):
    self.pids = [ 1000001, 1000005, 1000006, 1000011, 1000012, 1000015, 1000016, 
                  1000021, LSP, X2Z, X3Z, 1000035, X1W, X2W ]
    self.masses = {}
    self.names = { "gluino": 1000021, "squark": 1000001, "bottom", 1000005,
                   "stop": 1000006, "selectron": 1000011, "sneutrino": 1000012,
                   "stau": 1000015, "stau_neutrino": 1000016, "chi10": LSP,
                   "chi20": X2Z, "chi30": 1000035, "chi1+": X1W,
                   "chi2+": X2W }
    for i in self.pids:
        self.masses[i]=1e6

  def invent ( self ):
    model = { "gluino": 600, "chi10": 100, "gluino -> q q chi10": 1.0 }
    pass


if __name__ == "__main__":
    inventor = ModelInventor()
    inventor.invent()

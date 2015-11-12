#!/usr/bin/env python

'''
Created on 09/11/2015

@author: lessa
'''


import multiprocessing
import sys,glob
sys.path.append('../runTools')
from gridSmodels import runSmodelS,getSlhaFiles
from gridFastlim import prepareSLHA,runFastlim
from fastlimOutput import fastlimParser
import os



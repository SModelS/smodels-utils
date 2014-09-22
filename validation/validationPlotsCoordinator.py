#!/usr/bin/env python

"""
.. module:: validationPlot
     :synopsis: Module to create a validation plot for given grid data file. 

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>


"""

from __future__ import print_function
import setPath  # # set to python path for smodels
import logging
import types
from smodels_tools.tools.databaseBrowser import Browser

logger = logging.getLogger(__name__)
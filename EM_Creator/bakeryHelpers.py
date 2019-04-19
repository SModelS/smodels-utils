#!/usr/bin/env python3

"""
.. module:: helpers
        :synopsis: little helper snippets for the bakery.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

def dirName ( process, masses ):
    """ the name of the directory of one process + masses """
    return process + "." + "_".join(map(str,masses))

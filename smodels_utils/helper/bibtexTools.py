#!/usr/bin/env python3

"""
.. module:: bibtexTools
        :synopsis: Collection of methods for bibtex.
                   Currently contains only a dictionary for getting the
                   bibtex names of analyses

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def getBibtexName ( anaid ):
    """ get the bibtex name of anaid
    """
    names = { "ATLAS-SUSY-2016-07": "Aaboud:2017vwy",
              "ATLAS-SUSY-2016-16": "Aaboud:2017aeu",
              "CMS-SUS-16-050": "Sirunyan:2291344",
              "ATLAS-CONF-2013-047": "ATLAS-CONF-2013-047",
              "CMS-SUS-13-012": "Chatrchyan:2014lfa",
              "ATLAS-SUSY-2013-02": "Aad:2014wea",
    }
    if anaid in names:
        return names[anaid]
    return "FIXME"

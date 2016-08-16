#!/usr/bin/python

""" Conversion of fastlim SMS results to the SModelS framework,
    this is the main script """

import convertHelpers

exps = convertHelpers.all_exps
exps = [ "ATLAS_CONF_2013_024" ]

convertHelpers.runExps ( exps )

convertHelpers.closeDictionaryFile()

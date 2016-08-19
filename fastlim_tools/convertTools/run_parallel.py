#!/usr/bin/python

""" Conversion of fastlim SMS results to the SModelS framework,
    this is the main script """

import convertHelpers
import multiprocessing
import sys
import os

all_exps= convertHelpers.all_exps
# all_exps = [ "ATLAS_CONF_2013_024" ]

for i in all_exps:
    t=i.replace("_","-")
    convertHelpers.removeExp ( t )

# ncpus = multiprocessing.cpu_count()
ncpus = len ( convertHelpers.all_exps )
# ncpus = 1
p_exps = []
for i in range(ncpus):
    p_exps.append ( all_exps[i::ncpus] )

def runExample ( exps ):
    print "runExample",exps

children=[]

for exps in p_exps:
    pid = os.fork()
    if pid > 0:
        children.append ( pid )
    if pid == 0:
        convertHelpers.runExps ( exps )
        os._exit(0)

for child in children:
    r = os.waitpid ( child, 0 )

# convertHelpers.closeDictionaryFile()

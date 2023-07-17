#!/usr/bin/env python

"""
.. module:: checkConstraints
   :synopsis: Collects the contraints for Fastlim entries in the SModelS database

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import sys,os,glob
sys.path.append('../convertTools')
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels-database'))
sys.path.append(os.path.join(home,'smodels'))
from smodels.tools import databaseBrowser
from convertHelpers import smodels2fastlim


databasePath = os.path.join(home,'smodels-database')      
browser = databaseBrowser.Browser(databasePath)
browser.selectExpResultsWith(contact = ['fastlim'])

txs = {}
for expRes in browser:
    for dataset in expRes.datasets:
        for txname in dataset.txnameList: 
            tname = txname.txName
            const = txname.constraint
            if not tname in txs: txs[tname] = []
            if not const in txs[tname]: txs[tname].append(const)

for tname in txs:
    print smodels2fastlim(tname),tname,len(list(set(txs[tname]))),list(set(txs[tname]))
    

#!/usr/bin/env python3

""" get a certain element of a covariance matrix """

from smodels.experiment.databaseObj import Database

def get():
    d=Database("../../smodels-database")
    e=d.getExpResults ( anaId = "CMS-PAS-SUS-16-052" )
    

get()

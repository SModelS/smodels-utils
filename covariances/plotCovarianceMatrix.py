#!/usr/bin/env python3

""" some unfinished code that plots a covariance matrix as a 2d hist """

import sys
import numpy as np
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
import IPython
import matplotlib.pyplot as plt
import seaborn as sns

def plot():
    dbpath = "../../smodels-database"
    database = Database( dbpath, discard_zeroes = False)
    ana =  "CMS-SUS-16-048-ma5"
    res = database.getExpResults ( analysisIDs = [ ana ] )
    er = res[0]
    n = len ( er.globalInfo.covariance)
    # print ( er.globalInfo.datasetOrder )
    cov = er.globalInfo.covariance
    # fig, ax = plt.subplots()
    #grid_kws = {"hspace": .3, "vspace": 0.1 }
    #f, ax = plt.subplots(1, gridspec_kw=grid_kws)
    def fmtLabel ( s ):
        if s >= 1.:
            # return "%d" % s
            return "%.0f" % s
        if s < 1.:
            return ("%.1f" % s)[1:]
        return "%.1f" % s
    labels = [ [ fmtLabel(x) for x in y ] for y in cov ]
    cmap = "inferno"
    cmap = "rocket"
    annot_kws = { "fontsize": 10 }
    ax = sns.heatmap(cov, cmap=cmap, annot=labels, annot_kws=annot_kws, 
                     vmax = None, fmt='s' )
    def fmtTick ( x ):
        x = x.replace( "Ewkino", "e" ).replace("stop","t")
        x = x.replace( "MET", "" )
        x = x.replace( "PT_", "" ).replace("M_","")
        p1 = x.find("to")
        x = x[:p1]
        return x
    ax.invert_yaxis()
    #ax.invert_xaxis()
    ticklabels = [ fmtTick(x) for x in er.globalInfo.datasetOrder ]
    plt.title ( f"covariance matrix, {ana}" )
    ax.set_yticklabels ( ticklabels )
    ax.set_xticklabels ( ticklabels, rotation=75 )
    #b, t = plt.ylim()
    #print ( "bt", b, t )
    #plt.ylim ( b, t-5. )
    ax.figure.tight_layout()
    plt.savefig ( "histo2d.png" )


if __name__ == "__main__":
    plot()

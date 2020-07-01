#!/usr/bin/env python3

""" plot the meta statistics of database.dict """

from matplotlib import pyplot as plt
import numpy as np
import os
import scipy.stats
import matplotlib.mlab as mlab

class Plotter:
    def __init__ ( self, filename ):
        """
        :param filename: filename of dictionary
        """
        self.filename = filename
        self.read()

    def read ( self ):
        """ read in content of filename """
        with open( self.filename,"rt") as f:
            lines=f.readlines()
        self.meta=eval(lines[0])
        nan=float("nan")
        self.data=eval(lines[1])

    def computeP ( self, obs, bg, bgerr ):
        """ compute p value, for now we assume Gaussanity """
        simple = False ## approximation as Gaussian
        if simple:
            x = (obs - bg ) / np.sqrt ( bgerr**2 + bg )
            p = scipy.stats.norm.cdf ( x )
        else:
            return self.computePWithToys ( obs, bg, bgerr )
        return p

    def computePWithToys ( self, obs, bg, bgerr ):
        """ compute p value, for now we assume Gaussanity """
        fakes = []
        bigger = 0
        n= 10000
        lmbda = scipy.stats.norm.rvs ( loc=[bg]*n, scale=[bgerr]*n )
        # lmbda[np.where(lmbda<0.)] = 0.
        lmbda = lmbda[lmbda>0.]
        fakeobs = scipy.stats.poisson.rvs ( lmbda )
        return sum(fakeobs>obs) / len(fakeobs)

    def plot( self, variable ):
        """ plot the significances """
        S,P=[],[]
        for k,v in self.data.items():
            if not ":ul" in k:
                s = v[variable]
                S.append( s )
                obs = v["origN"]
                if not "orig" in variable:
                    obs = v["newObs"]
                P.append( self.computeP ( obs, v["expectedBG"], v["bgError"] ) )
                P.append( scipy.stats.norm.cdf ( s ) )
        mean,std = np.mean ( S), np.std ( S )
        minX, maxX = min(S), max(S)
        x = np.linspace( minX, maxX,100 )
        result = plt.hist( S, bins=30, label=f"{len(S)} SRs" )
        dx = result[1][1] - result[1][0]
        scale = len(S)*dx
        plt.plot(x,scipy.stats.norm.pdf(x,mean,std)*scale, label="%.2f $\pm$ %.2f" % ( mean, std ))
        plt.legend()
        dbname = os.path.basename ( self.meta["database"] )
        title = f"meta stats, real observations, database v{dbname}"
        if not "orig" in variable:
            title = f"meta stats, fake observations, database v{dbname}"
        if abs ( self.meta["fudge"] - 1. ) > 1e-3:
            title += " f=%.2f" % self.meta["fudge"]
        plt.title ( title )
        plt.xlabel ( "reduced distances $( n_\mathrm{obs} - n_\mathrm{bg} ) / \sqrt{ \mathrm{stat}^2 + \mathrm{sys}^2 } $" )
        plt.savefig ( f"{variable}.png" )
        plt.clf()
        plt.hist ( P, bins=10, label="%.2f $\pm$ %.2f" % ( np.mean(P), np.std(P) ) )
        plt.legend()
        plt.title  ( title )
        plt.xlabel ( "p values" )
        plt.savefig ( f"H{variable}.png" )
        plt.clf()

def main():
    plotter = Plotter ( "./database.dict" )
    plotter.plot( "origS" )
    plotter.plot( "S" )

if __name__ == "__main__":
    main()

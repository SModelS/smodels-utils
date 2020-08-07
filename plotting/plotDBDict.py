#!/usr/bin/env python3

""" plot the meta statistics of database.dict """

from matplotlib import pyplot as plt
import numpy as np
import os
import pickle
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

    def compute ( self, variable, fakeVariable, store ):
        """ compute the p values """
        S,Sfake,P,Pfake=[],[],[],[]
        fname = "pDatabase.pcl"
        if os.path.exists ( fname ):
            print ( f"[plotDBDict] found {fname}. Using data therein." )
            with open ( fname, "rb" ) as f:
                fname = os.path.basename ( pickle.load ( f ) )
                selfbase = os.path.basename ( self.filename )
                if selfbase != fname:
                    print ( f"[plotDBDict] we want {selfbase} pickle has {fname}. Wont use." )
                else:
                    S = pickle.load ( f )
                    Sfake = pickle.load ( f )
                    P = pickle.load ( f )
                    Pfake = pickle.load ( f )
                    f.close()
                    return S,Sfake,P,Pfake
        for k,v in self.data.items():
            if not ":ul" in k:
                s = v[variable]
                sfake = v[fakeVariable]
                S.append( s )
                Sfake.append( sfake )
                obs = v["origN"]
                if not "orig" in variable:
                    obs = v["newObs"]
                fakeobs = v["newObs"]
                P.append( self.computeP ( obs, v["expectedBG"], v["bgError"] ) )
                Pfake.append( self.computeP ( fakeobs, v["expectedBG"], v["bgError"] ) )
                P.append( scipy.stats.norm.cdf ( s ) )
                Pfake.append( scipy.stats.norm.cdf ( sfake ) )
        if store:
            with open ( fname, "wb" ) as f:
                pickle.dump ( os.path.basename ( self.filename ), f )
                pickle.dump ( S, f )
                pickle.dump ( Sfake, f)
                pickle.dump ( P, f )
                pickle.dump ( Pfake, f )
                f.close()
        return S,Sfake,P,Pfake

    def plot( self, variable, fakeVariable, outfile ):
        """ plot the p values """
        S,Sfake,P,Pfake=self.compute ( variable, fakeVariable, True )
        mean,std = np.mean ( S), np.std ( S )
        minX, maxX = min(S), max(S)
        x = np.linspace( minX, maxX,100 )
        # plt.legend()
        dbname = os.path.basename ( self.meta["database"] )
        title = f"$p$ values, database v{dbname}"
        fudge = 1.
        if "fudge" in self.meta:
            fudge = self.meta["fudge"]
        if abs ( fudge - 1. ) > 1e-3:
            title += ", fudge=%.2f" % fudge
        plt.hist ( P, bins=10, label="real", facecolor="tab:blue" )
        plt.hist ( Pfake, bins=10, label="fake", edgecolor="red", linewidth=3, histtype="step" )
        print ( "real Ps at %.3f +/- %.2f" % ( np.mean(P), np.std(P) ) )
        print ( "fake Ps at %.3f +/- %.2f" % ( np.mean(Pfake), np.std(Pfake) ) )
        # plt.hist ( P, bins=10, label="$\\bar{p} = %.2f \pm %.2f$" % ( np.mean(P), np.std(P) ) )
        plt.legend()
        plt.title  ( title )
        plt.xlabel ( "$p$ values" )
        print ( f"[plotDBDict.py] plotting {outfile}"  )
        plt.savefig ( outfile )
        plt.clf()

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="meta statistics plotter, i.e. the thing that plots origS.png, HorigS.png, S.png, HS.png")
    argparser.add_argument ( '-d', '--dictfile', nargs='?',
            help='input dictionary file [./database.dict]', 
            type=str, default='./database.dict' )
    argparser.add_argument ( '-o', '--outfile', nargs='?',
            help='output file [./pDatabase.png]', 
            type=str, default='./pDatabase.png' )
    args=argparser.parse_args()
    plotter = Plotter ( args.dictfile )
    plotter.plot( "origS", "S", args.outfile )

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

""" plots a time series of (for now) the masses, as a function of MCMC step """

from matplotlib import pyplot as plt
import helpers

class TimeSeries:

    def fetchModels( self ):
        with open("states.dict","rt") as f:
            models=eval(f.read())
            self.models = models
            return models

    def __init__ ( self ):
        self.fetchModels()

    def getPids ( self ):
        # return [ 1000006, 1000022 ]
        ret = set()
        for model in self.models:
            for pid in model["masses"]:
                ret.add ( pid )
        return list(ret)
        
    def plot ( self ):
        pids = self.getPids()
        M = {}
        for pid in pids:
            M[pid]=[]
        for model in self.models:
            for pid in pids:
                mass = float("nan")
                if pid in model["masses"]:
                    mass = model["masses"][pid]
                M[pid].append ( mass )
        xticks = range(len(M[pids[0]] ) )
        for pid in pids:
            plt.plot ( xticks, M[pid], label=helpers.toLatex(pid, addDollars=True ) )
        plt.xticks ( xticks )
        plt.legend()
        plt.title("Evolution of masses over the MCMC walk" )
        plt.xlabel( "MCMC step" )
        plt.ylabel( "m [GeV]" )
        plt.savefig ( "masses.png" )

def main():
    plotter = TimeSeries()
    plotter.plot()

if __name__ == "__main__":
    main()

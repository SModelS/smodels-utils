#!/usr/bin/env python3

""" plots a time series of (for now) the masses, as a function of MCMC step """

from matplotlib import pyplot as plt
import helpers, os

class TimeSeries:

    def fetchModels( self ):
        with open( self.dictfile,"rt") as f:
            models=eval(f.read())
            self.models = models
            return models

    def __init__ ( self, dictfile ):
        self.dictfile = dictfile
        self.fetchModels()

    def getPids ( self ):
        ret = set()
        lastModel = set()
        for model in self.models:
            thisModel = set()
            for pid,mass in model["masses"].items():
                if mass < 1e5:
                    thisModel.add ( pid )
            for pid in thisModel:
                if pid in lastModel:
                    ret.add ( pid )
            lastModel = thisModel
        return list(ret)
        
    def plot ( self ):
        pids = self.getPids()
        print ( "[plotTimeSeries] masses %s" % pids )
        M = {}
        for pid in pids:
            M[pid]=[]
        for model in self.models:
            for pid in pids:
                mass = float("nan")
                if pid in model["masses"]:
                    mass = model["masses"][pid]
                M[pid].append ( mass )
        xticks = list(range(1,1+len(M[pids[0]] ) ))
        for pid in pids:
            label = helpers.toLatex(pid, addDollars=True ) # +" ["+str(pid)+"]"
            # print ( "M", pid, M[pid] )
            plt.plot ( xticks, M[pid], label=label )
        plt.xticks ( xticks )
        plt.legend()
        plt.title("Evolution of masses over the MCMC walk" )
        plt.xlabel( "MCMC step" )
        plt.ylabel( "m [GeV]" )
        plt.savefig ( "masses.png" )

def create( dictfile, filepath ):
    """ create history dict file from files in filepath """
    import glob
    if filepath.endswith ( "/" ) or os.path.isdir ( filepath ):
        filepath += "/pmodel-*.py"
    files = glob.glob ( filepath )
    files.sort()
    with open ( dictfile, "wt" ) as g:
        g.write ( "[" )
        for f in files:
            if not "pmodel" in f:
                continue
            if not f.endswith (".py"):
                continue
            with open ( f, "rt" ) as fh:
                D = eval ( fh.read() )
                g.write ( str(D) + ",\n" )
        g.write ( "]\n" )
        g.close()

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='history time series plotter')
    argparser.add_argument ( '-f', '--dictfile',
            help='history file to plot [history.dict]',
            type=str, default="history.dict"  )
    argparser.add_argument ( '-c', '--create',
            help='create history from pmodels (give unix filepath)',
            type=str, default=None  )
    args = argparser.parse_args()
    if args.create != None:
        create ( args.dictfile, args.create )
    plotter = TimeSeries( args.dictfile )
    plotter.plot()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""Simple interface to line profiler

moduleauthor: Andre Lessa
"""
from line_profiler import LineProfiler
from walker.randomWalker import RandomWalker
from tools import helpers
import time,os


t0 = time.time()
# %% Set seed
seed = 123
helpers.seedRandomNumbers(seed)

# %% Remove files from previous run
if os.path.isfile('./run_test/H0.pcl'):
    os.remove('./run_test/H0.pcl')
if os.path.isfile('./run_test/walker0.log'):
    os.remove('./run_test/walker0.log')

# %% Set the walker
nsteps = 10
walker = RandomWalker(0,nsteps,dbpath='./run_test/database.pcl',
                        catch_exceptions=False,nevents=10000, rundir='./run_test')

# %% Set the profiler
prof = LineProfiler()
# %% Add functions to be profiled
prof.add_function(walker.walk)
prof.add_function(walker.onestep)
prof.add_function(walker.decideOnTakingStep)
prof.add_function(walker.manipulator.randomlyChangeModel)
prof.add_function(walker.predictor.predict)
prof.add_function(walker.predictor.computeSignificance)
prof.add_function(walker.predictor.combiner.findHighestSignificance)
prof.add_function(walker.predictor.combiner._findLargestZ)
prof.add_function(walker.predictor.combiner.getSignificance)
prof.add_function(walker.predictor.combiner.findMuHat)
prof.add_function(walker.predictor.updateModelPredictions)


# %% Run
prof.run('walker.walk()')

# %% Print results
with open('walk_short_approx_new.lprof','w') as f:
    prof.print_stats(f)
    f.write('\n\nTotal (real) time: %1.2f min' %((time.time()-t0)/60.0))

print('\n\nTotal (real) time: %1.2f min' %((time.time()-t0)/60.0))

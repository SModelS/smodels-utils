#!/usr/bin/env python3

import IPython
import pickle
import sys
import random
import numpy as np
from gplearn.genetic import SymbolicRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.utils.random import check_random_state
from mpl_toolkits.mplot3d import Axes3D
from gplearn.functions import make_function
import matplotlib.pyplot as plt
import graphviz
from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import GeV, fb

def fetchEfficiencyMap():
    """ fetch our efficiency map from the database """
    db = Database ( "unittest" )
    aId = [ "CMS-SUS-16-039" ]
    expres = db.getExpResults(analysisIDs = aId )[0]
    ds = expres.datasets[0]
    txn = ds.txnameList[4]
    return txn

def createSample( npoints=1000 ):
    """ create a training sample of npoints points
    """
    txn = fetchEfficiencyMap()
    X_train, y_train = [], []
    npoints = 1000
    while len(X_train)< npoints:
        mmother = random.uniform ( 200, 2000 )
        mlsp = mmother + 1
        while mlsp > mmother:
            mlsp = random.uniform ( 0, 1500 )
        mv = [ [ mmother*GeV, mlsp*GeV], [ mmother*GeV, mlsp*GeV ] ]
        ul = txn.getULFor ( mv )
        if type(ul) == type(None):
            continue
        X_train.append ( ( mmother, mlsp ) )
        y_train.append ( ul.asNumber(fb) )
    return X_train, y_train


def createArtificialSample ():
    rng = check_random_state(0)

    # Training samples
    X_train = rng.uniform(-1, 1, 100).reshape(50, 2)
    # y_train = X_train[:, 0]**2 - X_train[:, 1]**2 + X_train[:, 1] - 1
    y_train = 4 * np.exp ( -2 * X_train[:, 0] ) * X_train[:, 1] - 2 + rng.uniform ( -.1, 1, 50 )

    # Testing samples
    X_test = rng.uniform(-1, 1, 100).reshape(50, 2)
    # y_test = X_test[:, 0]**2 - X_test[:, 1]**2 + X_test[:, 1] - 1
    y_test = 4 * np.exp ( -2 * X_test[:, 0] ) * X_test[:, 1] - 2
    return X_train, y_train, X_test, y_test

class Regressor:
    def __init__ ( self, load ):
        if load:
            self.loadFromPickle()
        self.instantiateRegressor()

    def log ( self, *args ):
        print ( "[symbolic] " + "".join ( *args ) )

    def instantiateRegressor( self ):
        def _protected_exp(x1):
            with np.errstate(over='ignore'):
                return np.where(np.abs(x1) < 100, np.exp(x1), 0.)

        pexp = make_function(function=_protected_exp, name='exp', arity=1 )

        function_set = [ 'add', 'sub', 'mul', 'div', pexp, 'log' ]

        self.est_gp = SymbolicRegressor(population_size=5000,
                                   generations=20, stopping_criteria=0.01,
                                   p_crossover=0.7, p_subtree_mutation=0.1,
                                   p_hoist_mutation=0.05, p_point_mutation=0.1,
                                   max_samples=0.9, verbose=1, function_set = function_set,
                                   parsimony_coefficient=0.01, random_state=0)

    def storeToPickle ( self ):
        with open ( "expr.pcl", "wb" ) as f:
            pickle.dump ( self.est_gp, f )
            pickle.dump ( self.est_gp._program, f )
            f.close()

    def loadFromPickle ( self ):
        with open ( "expr.pcl", "rb" ) as f:
            self.est_gp = pickle.load ( f )
            self.program = pickle.load ( f )
            f.close()
        print ( "loaded", self.est_gp._program )

    def train ( self, X_train, y_train ):
        self.log ( "start training" )
        self.est_gp.fit(X_train, y_train)
        # print ( self.est_gp._program )

        from sympy import sympify, pprint, Add, Mul, Lambda, Symbol, exp, re, expand, simplify

        x,y = Symbol("x"), Symbol("y")

        locals = {
            "add": Add,
            "mul": Mul,
            "exp": exp,
            "sub": Lambda((x, y), x - y),
            "div": Lambda((x, y), x/y)
        }

        self.log ( "sympify" )
        expr = sympify( str ( self.est_gp._program ), locals=locals )
        self.log ( "expand, simplify" )
        # expr = expand ( simplify ( expr ) )
        print ()
        pprint ( expr )
        self.expr = expr
        self.log ( "end training" )

    def interact ( self ):
        IPython.embed ( using=False )
        
    def compare ( self, x=4, y=3 ):
        self.est_gp.predict(np.array([x,y]).reshape(1,-1))

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='symbolic regressor')
    argparser.add_argument ( '-t', '--train', help='train',
                             action="store_true" )
    argparser.add_argument ( '-i', '--interactive', help='interactive',
                             action="store_true" )
    args = argparser.parse_args()

    if args.train:
        X_train, y_train = createSample( 1000 )
        # X_test, y_test = createSample()
        regressor = Regressor( False )
        regressor.train( X_train, y_train )
        regressor.storeToPickle()
    else:
        regressor = Regressor( True )
    # regressor.compare()
    if args.interactive:
        regressor.interact()

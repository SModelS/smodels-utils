#!/usr/bin/env python3

import IPython
import pickle
import sys
import time
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
from sympy import sympify, pprint, Add, Mul, Lambda, Symbol, exp, re, expand, simplify, log
from sympy.abc import x, y
from sympy.utilities.autowrap import autowrap

class Regressor:
    def __init__ ( self, load ):
        """
        :param load: load from pickle file
        """
        if load:
            self.loadFromPickle()
        else:
            self.instantiateRegressor()

    def fetchEfficiencyMap( self ):
        """ fetch our efficiency map from the database """
        db = Database ( "unittest" )
        aId = [ "CMS-SUS-16-039" ]
        expres = db.getExpResults(analysisIDs = aId )[0]
        ds = expres.datasets[0]
        txn = ds.txnameList[4]
        self.txn = txn

    def createSample( self, npoints=1000 ):
        """ create a training sample of npoints points
        """
        self.fetchEfficiencyMap()
        X_train, y_train = [], []
        while len(X_train)< npoints:
            mmother = random.uniform ( 200, 2000 )
            mlsp = mmother + 1
            while mlsp > mmother:
                mlsp = random.uniform ( 0, 1500 )
            ul = self.getULFor ( mmother, mlsp, reporttime=False )
            if type(ul) == type(None):
                continue
            X_train.append ( ( mmother, mlsp ) )
            y_train.append ( ul )
        return X_train, y_train

    def getULFor ( self, mmother, mlsp, reporttime=False ):
        """ get upper limit for mother, lsp
        :param reporttime: report also time spent?
        """
        mv = [ [ mmother*GeV, mlsp*GeV], [ mmother*GeV, mlsp*GeV ] ]
        t0 = time.time()
        ul = self.txn.getULFor ( mv )
        dt = time.time() - t0
        if type(ul) == type(None):
            if reporttime:
                return None,dt
            else:
                return None
        if reporttime:
            return ul.asNumber(fb),dt
        return ul.asNumber(fb)

    def log ( self, *args ):
        print ( "[symbolic] " + " ".join ( map(str,args ) ) )

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
                                   parsimony_coefficient=0.3, random_state=0)

    def storeToPickle ( self ):
        with open ( "expr.pcl", "wb" ) as f:
            pickle.dump ( self.est_gp, f )
            pickle.dump ( self.expr, f )
            pickle.dump ( self.txn, f )
            #pickle.dump ( self.est_gp._program, f )
            #pickle.dump ( self.est_gp.n_features_, f )
            f.close()

    def loadFromPickle ( self ):
        with open ( "expr.pcl", "rb" ) as f:
            self.est_gp = pickle.load ( f )
            self.expr = pickle.load ( f )
            self.txn = pickle.load ( f )
            f.close()
        self.createFunc()
        self.log ( "loaded", self.est_gp._program )

    def train ( self, X_train, y_train ):
        self.log ( "start training" )
        self.est_gp.fit(X_train, y_train)
        # print ( self.est_gp._program )

        self.sympify ()
        self.log ( "end training" )

    def sympify ( self ):
        self.locals = {
            'sub': lambda x, y : x - y,
            'div': lambda x, y : x/y,
            'mul': lambda x, y : x*y,
            'add': lambda x, y : x + y,
            'neg': lambda x    : -x,
            'pow': lambda x, y : x**y,
#            "exp": lambda x: exp(abs(x)),
            "log": lambda x: log(abs(x)),
            "X0": x,
            "X1": y,
        }

        self.log ( "sympify" )
        expr = sympify( str ( self.est_gp._program ), locals=self.locals )
        self.log ( "expand, simplify" )
        # expr = expand ( simplify ( expr ) )
        print ()
        pprint ( expr )
        self.expr = expr
        self.createFunc()

    def createFunc( self):
        self.func = autowrap(self.expr, tempdir="/tmp/me", verbose=True )
        # self.func = autowrap(self.expr)

    def pprint ( self ):
        print ( str(regressor.est_gp) )

    def interact ( self ):
        IPython.embed ( colors="neutral" )
        #ret = self.est_gp.predict(np.array([x,y]).reshape(1,-1))
        #return ret[0],time.time()-t0

    def predict ( self, x, y, reporttime=False ):
        """ predict! """
        t0 = time.time()
        ret = self.est_gp.predict(np.array([x,y]).reshape(1,-1))[0]
        dt = time.time()-t0
        if reporttime:
            return ret,dt
        return ret

    def predictSympy ( self, x, y, reporttime=False ):
        """ predict via sympy func """
        t0=time.time()
        r=self.func(x,y)
        dt= time.time()-t0
        if reporttime:
            return r,dt
        return r

    def compare ( self, x=600, y=200 ):
        """ compare predicted with interpolated """
        gppred,gpt = self.predict ( x, y, reporttime=True )
        origpred,origt = self.getULFor ( x, y, reporttime=True )
        spred,stime = self.predictSympy ( x, y, reporttime=True )
        D={ "gppred": gppred, "gptime": gpt, "origpred": origpred,
            "origtime": origt, "spred": spred, "stime": stime }
        return D

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='symbolic regressor')
    argparser.add_argument ( '-t', '--train', help='train',
                             action="store_true" )
    argparser.add_argument ( '-i', '--interactive', help='interactive',
                             action="store_true" )
    args = argparser.parse_args()

    if args.train:
        regressor = Regressor( False )
        X_train, y_train = regressor.createSample( 100 )
        # X_test, y_test = createSample()
        regressor.train( X_train, y_train )
        regressor.storeToPickle()
    else:
        regressor = Regressor( True )
    # regressor.compare()
    if args.interactive:
        regressor.interact()

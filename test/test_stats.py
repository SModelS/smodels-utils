#!/usr/bin/python

from smodels.tools import statistics
import random
import math
import scipy.stats
import dataharvester

def main():
    writer = dataharvester.Writer_file("dates.root;dates.txt")
    nexperiments=10
    for i in range(nexperiments):
        print "Experiment #",i
        t=one_experiment ()
        t["nr"]=i
        writer.save ( t )
    dataharvester.Writer_close()


def one_experiment():
    lambdaSig=10
    lambdaBG=30
    nsig=scipy.stats.poisson.rvs(lambdaSig)
    nbg=scipy.stats.poisson.rvs(lambdaBG)
    Nobs=nsig+nbg
    Nexp=lambdaBG
    sigmaexp = 0.
    lumi = 20.
    alpha=.05
    ulAndre = statistics.getUL(Nobs, Nexp, sigmaexp,alpha)
    ulBayes = statistics.bayesianUpperLimit(Nobs,0.00001,Nexp,sigmaexp,1.-alpha)
    ulMad   = statistics.upperLimitMadAnalysis ( Nobs, Nexp, sigmaexp, 1.-alpha )
    t=dataharvester.Tuple("data")    
    t["ulAndre"]=ulAndre
    t["ulBayes"]=ulBayes
    t["ulMad"]=ulMad
    return t

if __name__ == "__main__":
	main()

#!/usr/bin/env python3

from smodels.tools.simplifiedLikelihoods import Data, UpperLimitComputer 

def main():
    alpha=.05
    computer = UpperLimitComputer(cl=1.-alpha )
    bg = 0.1
    err = 10.
    ul0 = 0.
    for sigN in range(0,10):
        m = Data( bg+sigN, bg, err**2, nsignal = 1. )
        ul = computer.ulSigma(m, marginalize=False )
        if sigN == 0:
            ul0 = ul
        dul = ul - ul0
        print ( "sigN %d, ul = %.3f, dul = %.3f " % ( sigN, ul, dul ) )


main()

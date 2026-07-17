#!/usr/bin/env python3

""" helpers for the whole yields business """

def outputFile ( mN2, mC1, mN1, options ):
    ret = f"{options['outputdir']}/TChiWZoff_{mN2}_{mN1}_{mC1}_{mN1}"
    return ret


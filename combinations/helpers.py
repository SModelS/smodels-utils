#!/usr/bin/env python3

""" helper functions """

def getParticleName ( pid ):
    names = { 1000001: "~dL", 2000001: "~dR", 1000002: "~uL",
              2000002: "~uR", 1000003: "~sL", 2000003: "~sR",
              1000004: "~cL", 2000004: "~cR", 1000005: "~b1",
              2000005: "~b2", 1000006: "~t1", 2000006: "~t2",
              1000011: "~eL", 2000011: "~eR", 1000012: "~nue",
              1000013: "~muL", 2000013: "~muR", 1000014: "~numu",
              1000015: "~tauL", 2000015: "~tauR", 1000016: "~nutau",
              1000021: "~g", 1000022: "~chi10", 1000023: "~chi20",
              1000025: "~chi30", 1000035: "~chi40", 1000024: "~chi1+",
              1000037: "~chi2+" }
    pid = abs(pid)
    if pid in names:
        return names[pid]
    return str(pid)

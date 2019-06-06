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

def toLatex ( pid, addDollars=False, addM=False ):
    """ get the latex version of particle name 
    :param addDollars: add dollars before and after
    :param addM: make it m(particle)
    """
    pname = pid
    if type(pid)==int:
        pname = getParticleName(pid)
    rpls = { "~nutau": "\\tilde{\\nu}_{\\tau}", "L": "_{L}", "R": "_{R}", "1": "_{1}", "2": "_{2}", "~nu": "\\tilde{\\nu}",
             "~chi": "\\tilde{\\chi}", "~mu": "\\tilde{\\mu}", "+": "^{+}", "3": "_{3}", 
             "0": "^{0}", "-": "^{-}" }
    keys = list ( rpls.keys() )
    keys.sort(key=len,reverse=True)
    for kr in keys:
        vr=rpls[kr]
        pname = pname.replace(kr,vr)
    if pname.find("~")==0:
        p1,p2=1,2
        pname="\\tilde{"+pname[p1:p2]+"}"+pname[p2:]
    if addM:
        pname = "m(" + pname + ")"
    if addDollars:
        pname = "$" + pname + "$"
    return pname

    return str(pid)

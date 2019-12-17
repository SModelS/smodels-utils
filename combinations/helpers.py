#!/usr/bin/env python3

""" helper functions """

def getParticleName ( pid, addSign=False, addSMParticles=False ):
    """ get the particle name of pid 
    :param addSign: add sign info in name
    :param addSMParticles: if True, then print also SM particle names
    """
    if type ( pid ) in [ list, tuple ]:
        # a list of pids? latexify them individually and concatenate
        pids = []
        for p in pid:
            if not addSMParticles and abs(p)<1000000: # skip the SM particles
                continue
            pname = getParticleName ( p, addSign )
            pids.append ( pname )
        return "(" + ",".join ( pids ) + ")"
    names = { 1000001: "~dL", 2000001: "~dR", 1000002: "~uL",
              2000002: "~uR", 1000003: "~sL", 2000003: "~sR",
              1000004: "~cL", 2000004: "~cR", 1000005: "~b1",
              2000005: "~b2", 1000006: "~t1", 2000006: "~t2",
              1000011: "~eL", 2000011: "~eR", 1000012: "~nue",
              1000013: "~muL", 2000013: "~muR", 1000014: "~numu",
              1000015: "~tauL", 2000015: "~tauR", 1000016: "~nutau",
              1000021: "~g", 1000022: "~chi10", 1000023: "~chi20",
              1000025: "~chi30", 1000035: "~chi40", 1000024: "~chi1+",
              1000037: "~chi2+",
              -1000001: "~dLbar", -2000001: "~dRbar", -1000002: "~uLbar",
              -2000002: "~uRbar", -1000003: "~sLbar", -2000003: "~sRbar",
              -1000004: "~cLbar", -2000004: "~cRbar", -1000005: "~b1bar",
              -2000005: "~b2bar", -1000006: "~t1bar", -2000006: "~t2bar",
              -1000011: "~eLbar", -2000011: "~eRbar", -1000012: "~nuebar",
              -1000013: "~muLbar", -2000013: "~muRbar", -1000014: "~numubar",
              -1000015: "~tauLbar", -2000015: "~tauRbar", -1000016: "~nutaubar",
              -1000021: "~g", -1000022: "~chi10", -1000023: "~chi20",
              -1000025: "~chi30", -1000035: "~chi40", -1000024: "~chi1-",
              -1000037: "~chi2-"
              }
    if addSMParticles:
        SMnames = { 1: "d", 2: "u", 3: "s", 4: "c", 5: "b", 6: "t",
                    11: "e", 13: "mu", 15: "tau", 12: "nue", 14: "numu",
                    16: "nutau", 21: "g", 22: "photon", 23: "Z", 25: "higgs",
                    24: "W" }
        import copy
        cp = copy.deepcopy ( SMnames )
        for k,v in cp.items():
            SMnames[-k]=v+"-"
            if k in [1,2,3,4,5,6,12,14,16]:
                SMnames[-k]=v+"bar"
        
    if not addSign:
        pid = abs(pid)
    if pid in names:
        ret = names[pid]
        return ret
    return str(pid)

def toLatex ( pid, addDollars=False, addM=False, addSign=False ):
    """ get the latex version of particle name 
    :param addDollars: add dollars before and after
    :param addM: make it m(particle)
    :param addSign: add a "-" sign for negative pids
    """
    if type ( pid ) in [ list, tuple ]:
        # a list of pids? latexify them individually and concatenate
        pids = []
        lpid = list ( pid )
        lpid.sort()
        for p in lpid:
            pids.append ( toLatex ( p, addDollars, addM, addSign ) )
        return "(" + ",".join ( pids ) + ")"
    pname = pid
    if type(pid)==int:
        pname = getParticleName(pid,addSign)
    # oldp = pname
    rpls = { "~nutau": "\\tilde{\\nu}_{\\tau}", "L": "_{L}", "R": "_{R}", 
             "1": "_{1}", "2": "_{2}", "~nu": "\\tilde{\\nu}", 
             "~nue": "\\tilde{\\nu}_{e}", "~tauL": "\\tilde{\\tau}L",
             "~numu": "\\tilde{\\nu}_{\\mu}",
             "bar": "^{*}",
             "~chi": "\\tilde{\\chi}", "~mu": "\\tilde{\\mu}", "+": "^{+}", 
             "3": "_{3}", "0": "^{0}", "-": "^{-}" }
    keys = list ( rpls.keys() )
    keys.sort(key=len,reverse=True)
    for kr in keys:
        vr=rpls[kr]
        pname = pname.replace(kr,vr)
    if False and pname.find("~")==0 and pname.find("bar")>0:
        p1,p2=1,2
        pname = pname.replace("bar","")
        pname="\\tilde{"+pname[p1:p2]+"}^{*}"+pname[p2:]
    if pname.find("~")==0:
        p1,p2=1,2
        pname="\\tilde{"+pname[p1:p2]+"}"+pname[p2:]
    if addM:
        pname = "m(" + pname + ")"
    if addDollars:
        pname = "$" + pname + "$"
    # print ( "tolatex", pid, pname, oldp )
    return pname

    return str(pid)

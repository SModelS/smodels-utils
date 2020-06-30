#!/usr/bin/env python3

""" various helper functions that do not fit in any of the more
    specific modules """

rthresholds = (1.7,) ## threshold for rmax

import copy, sys, math

def getParticleName ( pid, addSign=False, addSMParticles=False ):
    """ get the particle name of pid 
    :param addSign: add sign info in name
    :param addSMParticles: if True, then print also SM particle names
    """
    if type ( pid ) in [ list, tuple ]:
        # a list of pids? latexify them individually and concatenate
        pids = []
        for p in pid:
            if not addSMParticles and type(p) not in [ list, tuple ] and abs(p)<1000000: # skip the SM particles
                continue
            pname = getParticleName ( p, addSign, addSMParticles )
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
              1000037: "~chi2+", 2000021: "~g2", 3000006: "~t3",
              -1000001: "~dLbar", -2000001: "~dRbar", -1000002: "~uLbar",
              -2000002: "~uRbar", -1000003: "~sLbar", -2000003: "~sRbar",
              -1000004: "~cLbar", -2000004: "~cRbar", -1000005: "~b1bar",
              -2000005: "~b2bar", -1000006: "~t1bar", -2000006: "~t2bar",
              -1000011: "~eLbar", -2000011: "~eRbar", -1000012: "~nuebar",
              -1000013: "~muLbar", -2000013: "~muRbar", -1000014: "~numubar",
              -1000015: "~tauLbar", -2000015: "~tauRbar", -1000016: "~nutaubar",
              -1000021: "~g", -1000022: "~chi10", -1000023: "~chi20",
              -2000021: "~g", -3000006: "~t3bar",
              -1000025: "~chi30", -1000035: "~chi40", -1000024: "~chi1-",
              -1000037: "~chi2-", "+-2000006": "~t2^{(*)}",
              "+-1000006": "~t1^{(*)}", "+-?000006": "~t_{i}^{(*)}",
              "+-1000024": "~chi1^{\pm}", "+-1000005": "~b1^{(*)}",
              "+-2000005": "~b2^{(*)}", "+-?000005": "~b_{i}^{(*)}",
              "+-1000001": "~dL^{(*)}",
              "+-2000001": "~dR^{(*)}", "+-?000001": "~d_{i}^{(*)}",
              "+-1000002": "~uL^{(*)}",
              "+-2000002": "~uR^{(*)}", "+-?000002": "~u_{i}^{(*)}",
              "+-1000003": "~sL^{(*)}",
              "+-2000003": "~sR^{(*)}", "+-?000003": "~s_{i}^{(*)}",
              "+-1000004": "~cL^{(*)}",
              "+-2000004": "~cR^{(*)}", "+-?000004": "~c_{i}^{(*)}",
              "+-3000006": "~t3^{(*)}", "+-1000015": "~tau_{1}^{(*)}",
              "+-1000011": "~e_{1}^{(*)}", "+-1000013": "~mu_{1}^{(*)}",
              "+-1000037": "~chi2^{\pm}"
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
    if True:
        print ( "[helpers] could not find pid %s" % pid )
        # sys.exit()
    return str(pid)

def lrEquiv ( l, r ):
    """ check if the two strings are equivalent up to L vs R """
    if type(l) != str:
        return False
    if type(r) != str:
        return False
    if l.startswith("+-") and r.startswith("+-"):
        l=l.replace("+-","")
        r=r.replace("+-","")
    return l[1:] == r[1:]

def simplifyList ( modes ):
    """ simplify a given list of production modes """
    # print ( "reducing", modes )
    import itertools
    ret = copy.deepcopy ( modes )
    for combo in itertools.combinations ( modes, 2 ):
        if combo[0][0] == combo[1][0] and combo[0][1] == -combo[1][1]:
            try:
                ret.remove ( combo[0] )
                ret.remove ( combo[1] )
                ret.append ( ( combo[0][0], "+-%s" % abs(combo[1][1]) ) )
            except ValueError:
                pass
        if combo[0][0] == combo[1][1] and combo[0][1] == -combo[1][0]:
            try:
                ret.remove ( combo[0] )
                ret.remove ( combo[1] )
                ret.append ( ( combo[0][0], "+-%s" % abs(combo[1][0]) ) )
            except ValueError:
                pass
        if combo[0][1] == combo[1][1] and combo[0][0] == -combo[1][0]:
            try:
                ret.remove ( combo[0] )
                ret.remove ( combo[1] )
                ret.append ( ( combo[0][1], "+-%s" % abs(combo[1][0]) ) )
            except ValueError:
                pass
        if combo[0][0] == -combo[1][0] and combo[0][1] == -combo[1][1]:
            try:
                ret.remove ( combo[0] )
                ret.remove ( combo[1] )
                ret.append ( ( "+-%s" % abs(combo[0][0]), "+-%s" % abs(combo[1][0]) ) )
            except ValueError:
                pass
        if combo[0][0] == -combo[1][1] and combo[0][1] == -combo[1][0]:
            try:
                ret.remove ( combo[0] )
                ret.remove ( combo[1] )
                ret.append ( ( "+-%s" % abs(combo[0][0]), "+-%s" % abs(combo[1][0]) ) )
            except ValueError:
                pass
    modes = copy.deepcopy ( ret )
    for combo in itertools.combinations ( modes, 2 ):
        if type(combo[0][1])==str and type(combo[1][1])==str:
            if combo[0][1] == combo[1][1] and type(combo[0][0])==int and \
                            type(combo[1][0])==int and combo[0][0]==-combo[1][0]:
                try:
                    ret.remove ( combo[0] )
                    ret.remove ( combo[1] )
                    ret.append ( ( "+-%s" % abs(combo[0][0]), combo[0][1] ) )
                except ValueError as e:
                    pass
        if type(combo[0][0])==int and type(combo[1][1])==str:
            c00 = abs(combo[0][0])
            if combo[0] == (-c00, -c00) and combo[1] == (c00, '+-%s' % c00 ):
                try:
                    ret.remove ( combo[0] )
                    ret.remove ( combo[1] )
                    ret.append ( ( "+-%s" % abs(combo[0][0]), combo[1][1] ) )
                except ValueError as e:
                    pass
            if type(combo[0][1])==str and c00 == combo[1][0] and \
                     lrEquiv ( combo[0][1], combo[1][1] ):
                ## (1000021, '+-2000006'), (1000021, '+-1000006')
                try:
                    ret.remove ( combo[0] )
                    ret.remove ( combo[1] )
                    c11 = combo[1][1].replace("+-1","+-?").replace("+-2","+-?")
                    ret.append ( ( combo[0][0], c11 ) )
                except ValueError as e:
                    pass
    # print ( "reduced to", ret )
    return ret

def toHtml ( pid, addM=False, addSign=False, addBrackets=True ):
    """ get the HTML version of particle name 
    :param addM: make it m(particle)
    :param addSign: add a "-" sign for negative pids
    :param addBrackets: add brackets at beginning and end
    """
    if type ( pid ) in [ list ]: ## several production modes are given in lists
        pid = simplifyList ( pid )
        ret = ""
        for pids in pid:
            ret += toHtml ( pids, addM, addSign )
            ret += "="
        if len(ret)>1:
            ret = ret[:-1]
        return ret
            
    if type ( pid ) in [ set, tuple ]: ## production mothers are given as tuples
        # a list of pids? latexify them individually and concatenate
        pids = []
        lpid = list ( pid )
        try:
            lpid.sort()
        except:
            pass
        for p in lpid:
            pids.append ( toHtml ( p, addM, addSign ) )
        ret = ",".join ( pids ) 
        if addBrackets:
            ret = "(" + ret + ")"
        return ret
    pname = pid
    if type(pid) in [ int, str ]:
        pname = getParticleName(pid,addSign)
    pname = pname.replace("1","<sub>1</sub>" )
    pname = pname.replace("2","<sub>2</sub>" )
    pname = pname.replace("L","<sub>L</sub>" )
    pname = pname.replace("R","<sub>R</sub>" )
    pname = pname.replace("chi","&chi;" )
    pname = pname.replace("mu","&mu;" )
    pname = pname.replace("tau","&tau;" )
    pname = pname.replace("0","<sup>0</sup>" )
    pname = pname.replace("bar","<sup>*</sup>" )
    return pname

def toLatex ( pid, addDollars=False, addM=False, addSign=False,
              addBrackets = True ):
    """ get the latex version of particle name 
    :param addDollars: add dollars before and after
    :param addM: make it m(particle)
    :param addSign: add a "-" sign for negative pids
    :param addBrackets: add brackets at beginning and end
    """

    if type ( pid ) in [ list ]: ## several production modes are given in lists
        pid = simplifyList ( pid )
        ret = ""
        for pids in pid:
            ret += toLatex  ( pids, addDollars, addM, addSign )
            ret += "="
        if len(ret)>1:
            ret = ret[:-1]
        return ret
            
    if type ( pid ) in [ set, tuple ]: ## production mothers are given as tuples
        # a list of pids? latexify them individually and concatenate
        pids = []
        lpid = list ( pid )
        try:
            lpid.sort()
        except:
            pass
        for p in lpid:
            pids.append ( toLatex ( p, addDollars, addM, addSign ) )
        ret = ",".join ( pids )
        if addBrackets:
            ret = "(" + ret + ")"
        return ret
    pname = pid
    if type(pid) in [ int, str ]:
        pname = getParticleName(pid,addSign)
    # oldp = pname
    rpls = { "~nutau": "\\tilde{\\nu}_{\\tau}", "L": "_{L}", "R": "_{R}", 
             "1": "_{1}", "2": "_{2}", "~nu": "\\tilde{\\nu}", 
             "~nue": "\\tilde{\\nu}_{e}", "~tauL": "\\tilde{\\tau}L",
             "~numu": "\\tilde{\\nu}_{\\mu}", "~tau1": "\\tilde{\\tau}1",
             "bar": "^{*}", "~tau2": "\\tilde{\\tau}2",
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

def findLargestExcess ( db ):
    """ find the largest excess in any efficiency map type result
        in the given database 
    :param db: a SModelS database object
    :returns: the dataset object
    """
    results = db.getExpResults ( dataTypes = [ "efficiencyMap" ] )
    excesses = {}
    for expRes in results:
        datasets = expRes.datasets
        for dataset in datasets:
            nobs = dataset.dataInfo.observedN
            nbg = dataset.dataInfo.expectedBG
            bgErr = dataset.dataInfo.bgError
            S = 0.
            toterr = math.sqrt ( bgErr**2 + nbg )
            if toterr > 0.:
                S = ( nobs - nbg ) / toterr
            if S < 1.:
                continue
            if not S in excesses:
                excesses[S]=[]
            excesses[S].append ( dataset )

    def pprint ( excesses ):
        keys = list ( excesses.keys() )
        keys.sort()
        for k in keys[-5:]:
            ds = excesses[k]
            if len(ds)!=1:
                print ( "error cannot handle" )
                continue
            ds = ds[0]
            obsN = ds.dataInfo.observedN
            eBG = ds.dataInfo.expectedBG
            print ( "Z=%.2f: %15s, %s: %d/%.2f" % \
                    ( k, ds.globalInfo.id, str(ds.dataInfo.dataId), obsN, eBG ) )

    pprint ( excesses )
    print ( "[helpers.findLargestExcess] found %d eff maps" % len(results) )
    return excesses

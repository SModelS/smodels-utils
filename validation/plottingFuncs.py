#!/usr/bin/env python3

"""
.. module:: plottingFuncs
   :synopsis: Main methods for dealing with the plotting of a validation plot

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging,os,sys,numpy,random,copy
sys.path.append('../')
from array import array
import math, ctypes
logger = logging.getLogger(__name__)
from ROOT import (TFile,TGraph,TGraph2D,gROOT,TMultiGraph,TCanvas,TLatex,
                  TLegend,kGreen,kRed,kOrange,kBlack,kGray,TPad,kWhite,gPad,
                  TPolyLine3D,TColor,gStyle,TH2D,TImage,kBlue )
from smodels.tools.physicsUnits import fb, GeV, pb
#from smodels.theory.auxiliaryFunctions import coordinateToWidth,withToCoordinate
from smodels_utils.dataPreparation.massPlaneObjects import MassPlane
from smodels_utils.helper.prettyDescriptions import prettyTxname, prettyAxes
try:
    from smodels.theory.auxiliaryFunctions import unscaleWidth,rescaleWidth
except:
    pass
try:
    from smodels.theory.auxiliaryFunctions import removeUnits
except:
    from backwardCompatibility import removeUnits


#Set nice ROOT color palette for temperature plots:
stops = [0.00, 0.34, 0.61, 0.84, 1.00]
red   = [0.00, 0.00, 0.87, 1.00, 0.51]
green = [0.00, 0.81, 1.00, 0.20, 0.00]
blue  = [0.51, 1.00, 0.12, 0.00, 0.00]
s = array('d', stops)
r = array('d', red)
g = array('d', green)
b = array('d', blue)
TColor.CreateGradientColorTable(len(s), s, r, g, b, 999)
gStyle.SetNumberContours(999)

def clean ( obj ):
    """ check for some issues with the exclusion line
    :param obj: the ROOT.TGraph
    """
    ret = obj.ReadObj()
    n = ret.GetN()
    # x, y = Double(), Double()
    x, y = ctypes.c_double(), ctypes.c_double()
    for i in range(n):
        ret.GetPoint(i,x,y)
        if x.value < 0.:
            print ( "[plottingFuncs] ERROR: x value %s of exclusion line smaller than zero? do you really want this? Will set to zero." % x.value )
            ret.SetPoint ( i, 0., y.value )
        if y.value < 0.:
            print ( "[plottingFuncs] ERROR: y value %s of exclusion line smaller than zero? do you really want this? Will set to zero." % y.value )
            ret.SetPoint ( i, x.value, 0. )
    return ret

def getExclusionCurvesFor(expResult,txname=None,axes=None, get_all=False ):
    """
    Reads sms.root and returns the TGraph objects for the exclusion
    curves. If txname is defined, returns only the curves corresponding
    to the respective txname. If axes is defined, only returns the curves

    :param expResult: an ExpResult object
    :param txname: the TxName in string format (i.e. T1tttt)
    :param axes: the axes definition in string format (e.g. [x, y, 60.0], [x, y, 60.0]])
    :param get_all: Get also the +-1 sigma curves?

    :return: a dictionary, where the keys are the TxName strings
            and the values are the respective list of TGraph objects.
    """

    if type(expResult)==list:
        expResult=expResult[0]
    rootpath = os.path.join(expResult.path,'sms.root')
    if not os.path.isfile(rootpath):
        logger.error("Root file %s not found" %rootpath)
        return False

    rootFile = TFile(rootpath)
    txnames = {}
    #Get list of TxNames (directories in root file)
    for obj in rootFile.GetListOfKeys():
        objName = obj.ReadObj().GetName()
        if txname and txname != objName: continue
        txnames[objName] = obj.ReadObj()
    if not txnames:
        logger.warning("Exclusion curve for %s not found in %s" %(txname,rootpath))
        return False

    #For each Txname/Directory get list of exclusion curves
    nplots = 0
    for tx,txDir in txnames.items():
        txnames[tx] = []
        for obj in txDir.GetListOfKeys():
            objName = obj.ReadObj().GetName()
            if not 'exclusion' in objName.lower(): continue
            if (not get_all) and (not 'exclusion_' in objName.lower()): continue
            if 'expexclusion' in objName.lower(): continue
            # print "[plottingFuncs.py] name=",objName
            if axes and not axes in objName: continue
            T = clean ( obj )
            txnames[tx].append( T )
            # txnames[tx].append(obj.ReadObj())
            nplots += 1
    if not nplots:
        logger.warning("No exclusion curve found.")
        return False

    return txnames

def getFigureUrl(validationPlot ):

    txname = validationPlot.expRes.datasets[0].txnameList[0]
    txurl = txname.getInfo("figureUrl")
    txaxes = txname.getInfo("axes")
    if isinstance(txurl,str):
        return txname.getInfo("figureUrl" )
    if not txurl:
        return None
    if type(txurl) != type(txaxes):
        logger.error("figureUrl (%s) and axes (%s) are not of the same type" %(txurl,
                       txaxes))
        return None
    elif isinstance(txurl,list) and len(txurl) != len(txaxes):
        logger.error("figureUrl (%s) and axes (%s) are not of the same length" %(txurl,
                       txaxes))
        return None
    if not validationPlot.axes in txaxes:
        return None
    pos = [i for i,x in enumerate(txaxes) if x==validationPlot.axes ]

    if len(pos)!=1:
        logger.error("found axes %d times. Did you declare several maps for the same analysis/dataset/topology combo? Will exit, please fix!" % len(pos))
        sys.exit()
    return txurl[pos[0]]

def createSpecialPlot(validationPlot,silentMode=True,looseness=1.2,what = "bestregion", nthpoint =1,
       signal_factor = 1. ):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurves to generate "special" plots, showing
    e.g. upper limits or best signal region

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param what: what is to be plotted("bestregion", "upperlimits", "crosssections")
    :param nthpoint: label only every nth point
    :param signal_factor: an additional factor that is multiplied with the signal cross section,
    when comparing with the upper limit. Makes it easier to account for multiplicative factors,
    like the number of squark flavors in production
    :return: TCanvas object containing the plot
    """
    kfactor=None

    excluded, allowed = TGraph(), TGraph()
    excluded_border, allowed_border = TGraph(), TGraph()
    cond_violated=TGraph()
    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
    else:
        # Get excluded and allowed points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            if isinstance(pt['axes'],dict):
                if len(pt['axes']) == 1:
                    x, y = pt['axes']['x'],pt['signal']/pt['UL']
                else:
                    x, y = pt['axes']['x'],pt['axes']['y']
            else:
                x,y = pt['axes']
            if pt['condition'] and max(pt['condition'].values())> 0.05:
                logger.warning("Condition violated for file " + pt['slhafile'])
                cond_violated.SetPoint(cond_violated.GetN(), x, y)
            elif signal_factor * pt['signal'] > pt['UL']:
                if signal_factor * pt['signal'] < pt ['UL']* looseness:
                    excluded_border.SetPoint(excluded_border.GetN(), x, y)
                else:
                    excluded.SetPoint(excluded.GetN(), x, y )
            else:
                if signal_factor * pt['signal']*looseness > pt['UL']:
                    allowed_border.SetPoint(allowed_border.GetN(), x, y)
                else:
                    allowed.SetPoint(allowed.GetN(), x, y)

    labels=[]

    # print "validationPlot.officialCurves=",validationPlot.officialCurves

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        if isinstance(official,list): official = official[0]

    if silentMode: gROOT.SetBatch()
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    if official:
        setOptions(official, Type='official')
    base = TMultiGraph()
    if allowed.GetN()>0: base.Add(allowed, "P")
    if excluded.GetN()>0: base.Add(excluded, "P")
    if allowed_border.GetN()>0: base.Add(allowed_border, "P")
    if excluded_border.GetN()>0: base.Add(excluded_border, "P")
    if cond_violated.GetN()>0: base.Add(cond_violated, "P")
    if official:
        baseiAdd(official, "L")
    title = what+"_"+validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
            # + "_" + validationPlot.axes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    base.Draw("AP")
    base.SetTitle(title)
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    base.l=l
    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.02)
        l1.DrawLatex(.12,.1,"%s" % figureUrl)
        base.l1=l1

    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
    else:
        # Get excluded and allowed points:
        for ctr,pt in enumerate(validationPlot.data):
            if ctr%nthpoint != 0:
                continue
            if kfactor == None:
                kfactor = pt ['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()
            if isinstance(pt['axes'],dict):
                if len(pt['axes']) == 1:
                    x, y = pt['axes']['x'],pt['signal']/pt['UL']
                else:
                    x, y = pt['axes']['x'],pt['axes']['y']
            else:
                x,y = pt['axes']
            import ROOT
            lk=ROOT.TLatex ()
            lk.SetTextSize(.01)
            if what in [ "bestregion", "bestcut" ]:
                bestregion=pt["dataset"].replace("ANA","").replace("CUT","")
                lk.DrawLatex(x, y, bestregion )
            elif what == "upperlimits":
                ul=pt["UL"].asNumber(pb)
                lk.DrawLatex(x, y, str(ul) )
            elif what == "crosssections":
                signalxsec=pt['signal'].asNumber(pb)
                lk.DrawLatex(x, y, str(signalxsec) )
            elif what == "efficiencies":
                eff = pt['efficiency']
                if isinstance(eff,float):
                    eff = format(eff,'1.0e')
                else:
                    eff = str(eff)
                lk.DrawLatex(x, y, eff)
            else:
                logger.error( "dont know how to draw %s" % what )
                sys.exit()
            labels.append(lk )

        #Add original grid data to UL plot:
        if what == "upperlimits": ## FIXME this doesnt work anymore
            olk=ROOT.TLatex ()
            olk.SetTextSize(.02)
            massPlane = MassPlane.fromString(validationPlot.axes)
            txnameObjs = validationPlot.expRes.getTxnameWith({'txName': validationPlot.txName})
            for txnameObj in txnameObjs:
                txnameData = txnameObj.txnameData.data
                if txnameData==None:
                        continue
                for (itr, (mass,ul)) in enumerate(txnameData ):
                    if itr% nthpoint != 0: continue
                    mass_unitless = [[(m/GeV).asNumber() for m in mm] for mm in mass]
                    varsDict = massPlane.getXYValues(mass_unitless)
                    if not varsDict:
                        continue
                    x ,y = varsDict['x'],varsDict['y']
                    ul = ul.asNumber(pb)
                    lk.DrawLatex(x, y, "#color[4]{%.2f}" % ul )

    l2=TLatex()
    l2.SetNDC()
    l2.SetTextSize(.04)
    l2.DrawLatex(.15,.78,"k-factor %.2f" % kfactor)
    base.l2=l2
    l3=TLatex()
    l3.SetNDC()
    l3.SetTextSize(.04)
    if what == "upperlimits":
        drawingwhat="upper limits [pb]"
    if what == "crosssections":
        drawingwhat="theory predictions [pb]"
    if what in [ "bestregion", "bestcut" ]:
        drawingwhat="best signal region"
    else:
        drawingwhat = what
    l3.DrawLatex(.15,.7, drawingwhat )
    base.l3=l3
    if abs(signal_factor-1.0)>.0001:
        l4=TLatex()
        l4.SetNDC()
        l4.SetTextSize(.04)
        l4.DrawLatex(.15,.62, "signal factor %.1f" % signal_factor )
        base.l4=l4

    plane.base = base

    if not silentMode:
        _ = raw_input("Hit any key to close\n")

    plane.labels=labels

    return plane

def getXYFromSLHAFile ( slhafile, vPlot ):
    """ get coordinates from the slhafile name, given
        a validationPlot object vPlot """
    tokens = slhafile.replace(".slha","").split("_" )
    if vPlot.txName in [ "THSCPM1b", "THSCPM2b" ]:
        ## work around an issue with THSCPM1b, they only
        ## give one branch in the slha file names
        tokens += tokens[-2:]
    if vPlot.txName in [ "THSCPM6" ]:
        ## work around an issue with THSCPM1b, they only
        ## give one branch in the slha file names
        tokens = tokens[:5] + [ tokens[5] ]*2 + [ tokens [ 6 ] ] * 2
    masses = list ( map ( float, tokens[1:] ) )
    massPlane = MassPlane.fromString( vPlot.txName, vPlot.axes )
    nM = int ( len(masses)/2 ) ## number of masses per branch
    if vPlot.txName in [ "T5GQ" ]:
        nM+=1
    if len(masses) % 2 != 0:
        logger.debug("asymmetrical branch. Dont know how to handle" )
    #if masses[:nM] != masses[nM:]: ## actually seems to work
    #    logger.warning("asymmetrical branch %s != %s. Dont know how to handle" % ( masses[:nM], masses[nM:] ) )
    widths = None
    if "(" in vPlot.axes and ")" in vPlot.axes: ## width dependent result
        from sympy import var
        x__,y__,z__,x__ = var( "x y z w" )
        ax = eval ( vPlot.axes )
        widths = []
        widthsbr, massbr = [], []
        tmpmasses = []
        # print ( "ax=", ax )
        ctr = 0
        for br in ax:
            for v in br:
                if type(v) == tuple:
                    massbr.append ( masses[ctr] )
                    ctr += 1
                    widthsbr.append ( masses[ctr] )
                else:
                    massbr.append ( masses[ctr] )
                ctr += 1
            widths.append ( widthsbr )
            widthsbr = []
            tmpmasses.append ( massbr )
            massbr = []
        masses = tmpmasses
    else:
        masses = [ masses[:nM], masses[nM:] ]
    if vPlot.txName in [ "THSCPM6" ]:
        masses = [ list(map(float,tokens[1:4 ] ) ) ] * 2
        widths = [ list(map(float,[ tokens[5] ] ) ) ] * 2
    if vPlot.txName in [ "THSCPM5" ]:
        masses = [ list(map(float,tokens[1:4 ] ) ) ] * 2
        widths = [ list(map(float,[ tokens[4] ] ) ) ] * 2
    if vPlot.txName in [ "THSCPM7" ]:
        masses = list(map(float,tokens[1:4 ] ) ), [ float(tokens[1]), float(tokens[3]) ]
        # masses = [ [ float(tokens[1]), float(tokens[3]) ], [ list(map(float,tokens[1:4 ] ) ) ] ]
        widths = [ list(map(float,[ tokens[4] ] ) ) ] * 2
    if vPlot.txName in [ "THSCPM8", "THSCPM3" ]:
        masses = [ list(map(float,tokens[1:3 ] ) ) ] * 2
        widths = [ list(map(float,[ tokens[3] ] ) ) ] * 2
    # print ( "[plottingFuncs] slhafile", slhafile )
    # print ( "[plottingFuncs] masses", masses )
    # print ( "[plottingFuncs] widths", widths )
    varsDict = massPlane.getXYValues( masses, widths )
    # print ( "[plottingFuncs] -> vars", varsDict )
    ## FIXME take into account axis
    return varsDict

def getGridPoints ( validationPlot ):
    """ retrieve the grid points of the upper limit / efficiency map.
        currently only works for upper limit maps. """
    ret = []
    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    for dataset in validationPlot.expRes.datasets:
        txNameObj = None
        for ctr,txn in enumerate(dataset.txnameList):
            if txn.txName == validationPlot.txName:
                txNameObj = dataset.txnameList[ctr]
                break
        if txNameObj == None:
            logger.info ( "no grid points: did not find txName" )
            return []
        if not txNameObj.txnameData._keep_values:
            logger.info ( "no grid points: _keep_values is set to False" )
            return []
        if not hasattr ( txNameObj.txnameData, "origdata"):
            logger.info ( "no grid points: cannot find origdata (maybe try a forced rebuild of the database via runValidation.py -f)" )
            return []
        origdata =eval( txNameObj.txnameData.origdata)
        for ctr,pt in enumerate(origdata):
            masses = removeUnits ( pt[0], standardUnits=GeV )
            coords = massPlane.getXYValues(masses)
            if not coords == None and not coords in ret:
                ret.append ( coords )
    logger.info ( "found %d gridpoints" % len(ret) )
    ## we will need this for .dataToCoordinates
    return ret

def createUglyPlot( validationPlot,silentMode=True, looseness = 1.2, extraInfo=False,
                    preliminary=False, weightedAgreementFactor=False ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate the "ugly" exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param extraInfo: add additional info to plot: agreement factor, time spent,
                      time stamp, hostname
    :param preliminary: if true, write "preliminary" over the plot
    :param weightedAgreementFactor: weight points for the agreement factor with
                                    the area of their Voronoi cell
    :return: TCanvas object containing the plot
    """
    #title = validationPlot.expRes.globalInfo.id + "_" \
    #        + validationPlot.txName\
    #        + "_" + validationPlot.axes
    logger.info ( "now create ugly plot for %s, %s: %s" % \
       ( validationPlot.expRes.globalInfo.id, validationPlot.txName, validationPlot.axes ) )
    origdata = getGridPoints ( validationPlot )
    # validationPlot.axes="[[(x,y)], [(x,y)]]"

    # Check if data has been defined:
    xlabel, ylabel = 'x','y'
    excluded, allowed, excluded_border, allowed_border = TGraph(), TGraph(), TGraph(), TGraph()
    gridpoints = TGraph()
    noresult = TGraph() ## queried but got no result
    excluded.SetName("excluded")
    allowed.SetName("allowed")
    noresult.SetName("noresult")
    excluded_border.SetName("excluded_border")
    allowed_border.SetName("allowed_border")
    gridpoints.SetName ( "gridpoints" )
    cond_violated=TGraph()
    kfactor=None
    tavg = 0.

    countPts = 0 ## count good points

    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        # x,y = get
        return (None,None)
        ## sys.exit()

    nErrors = 0
    # Get excluded and allowed points:
    nmax = len(validationPlot.data)
    if False:
        nmax = 20
    dn = 50
    print ( " "*int(45+nmax/dn), end="<\r" )
    print ( "[plottingFuncs] checking validation points >", end="" )
    hasIssued1dErrorMsg = False ## error msg to appear only once
    for ctPoints,pt in enumerate(validationPlot.data):
        if ctPoints % dn == 0:
            print ( ".", end="", flush=True )
        if ctPoints == nmax:
            print ( "[plottingFuncs] emergency break" )
            break
        if "error" in pt.keys():
            vD = getXYFromSLHAFile ( pt["slhafile"], validationPlot )
            # print ( "vD", vD, pt["slhafile"], validationPlot.axes )
            if vD != None:
                # print ( "adding no-result point", noresult.GetN(), vD )
                x_, y_ = copy.deepcopy ( vD["x"] ), None
                if "y" in vD.keys():
                    y_ = copy.deepcopy ( vD["y"] )
                if y_ is None:
                    if not hasIssued1dErrorMsg:
                        logger.error ( "the data is 1d. FIXME cannot handle" )
                        hasIssued1dErrorMsg = True
                    y_ = 0.
                noresult.SetPoint(noresult.GetN(), x_, y_ )
            nErrors += 1
            continue
        countPts += 1
        if kfactor == None:
            kfactor = pt ['kfactor']
        if abs(kfactor - pt['kfactor'])> 1e-5:
            logger.error("kfactor not a constant throughout the plane!")
            sys.exit()

        xvals = pt['axes']
        if "t" in pt:
            tavg += pt["t"]
        if pt["UL"] == None:
            logger.warning ( "No upper limit for %s" % xvals )
            continue
        r = pt['signal']/pt ['UL']
        # print ( "x,y,r",r )
        if isinstance(xvals,dict):
            if len(xvals) == 1:
                x,y = xvals['x'],r
                ylabel = "r = #sigma_{signal}/#sigma_{UL}"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                elif "w" in xvals:
                    y = xvals['w']
        else:
            x,y = pt['axes']


        if pt['condition'] and pt['condition'] > 0.05:
            logger.warning("Condition violated at %f for file %s" % ( pt['condition'], pt['slhafile']) )
            cond_violated.SetPoint(cond_violated.GetN(), x, y)
        elif r > 1.:
            if r < looseness:
                excluded_border.SetPoint(excluded_border.GetN(), x, y)
            else:
                excluded.SetPoint(excluded.GetN(), x, y )
        else:
            if r> 1./looseness:
                allowed_border.SetPoint(allowed_border.GetN(), x, y)
            else:
                allowed.SetPoint(allowed.GetN(), x, y)

    print ( "< done!" )

    massPlane = MassPlane.fromString( validationPlot.txName, validationPlot.axes )
    for ctr,coords in enumerate(origdata):
        #masses = removeUnits ( pt[0], standardUnits=GeV )
        #coords = massPlane.getXYValues(masses)
        if coords != None and "y" in coords:
            gridpoints.SetPoint( gridpoints.GetN(), coords["x"], coords["y"] )

    if countPts == 0:
        logger.warning ( "no good points??" )
        return ( None, None )
    tavg = tavg / len (validationPlot.data )

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        logger.debug("Official curves have length %d" % len (official) )

    if silentMode: gROOT.SetBatch()
    setOptions(allowed, Type='allowed')
    setOptions(cond_violated, Type='cond_violated')
    setOptions(allowed_border, Type='allowed_border')
    setOptions(excluded, Type='excluded')
    setOptions(excluded_border, Type='excluded_border')
    setOptions(noresult, Type='noresult')
    base = TMultiGraph()
    if official:
        for i in official:
            setOptions( i, Type='official')
    setOptions(gridpoints, Type='gridpoints')
    dx = .12 ## top, left
    nleg = 5
    from sympy import var
    xvar_,yvar_,zvar_ = var( "xvar_ yvar_ zvar_" )
    g=eval(validationPlot.axes.replace("x","xvar_").replace("y","yvar_").replace("z","zvar_"))
    reverse = (g[1][0]==yvar_) ## do reverse if [x,*],[y,*] type of plot (eg TGQ)
    if reverse: ## if it is an [x,*],[y,*] plot, put legend to right, not left
        dx = .53
    leg = TLegend( dx,0.82-0.040*nleg,0.35+dx,0.88)
    setOptions(leg)
    leg.SetTextSize(0.04)
    if allowed.GetN()>0:
        base.Add(allowed, "P")
        leg.AddEntry ( allowed, "allowed", "P" )
    if excluded.GetN()>0:
        base.Add(excluded, "P")
        leg.AddEntry ( excluded, "excluded", "P" )
    if allowed_border.GetN()>0:
        base.Add(allowed_border, "P")
        leg.AddEntry(allowed_border, "allowed (but close)", "P")
    if excluded_border.GetN()>0:
        base.Add(excluded_border, "P")
        leg.AddEntry(excluded_border, "excluded (but close)", "P")
    if cond_violated.GetN()>0:
        base.Add(cond_violated, "P")
        leg.AddEntry( cond_violated, "condition violated", "P" )
    if noresult.GetN()>0:
        base.Add(noresult, "P")
        leg.AddEntry( noresult, "no result", "P" )
    if official:
        for i in official:
            base.Add( i, "L")
    if not official == None:
        for ctr,i in enumerate(official):
            completed = copy.deepcopy ( i )
            validationPlot.completeGraph ( completed )
            completed.SetLineColor( kGray )
            completed.SetLineStyle( 3 ) # show also how plot is completed
            completed.Draw("LP SAME" )
            #i.Draw("LP SAME" )
            if ctr == 0:
                leg.AddEntry ( i, "official exclusion", "L" )
    if gridpoints.GetN()>0:
        base.Add(gridpoints, "P")
        leg.AddEntry(gridpoints, "%d SModelS grid points" % gridpoints.GetN(), "P")
    title = validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.axes
            #+ "_" + validationPlot.niceAxes
    subtitle = "%d datasets: " % len(validationPlot.expRes.datasets)
    if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ):
        ## pyhf combination
        subtitle = "pyhf combining %d SRs: " % len(validationPlot.expRes.datasets)
    for dataset in validationPlot.expRes.datasets:
        ds_txnames = map ( str, dataset.txnameList )
        if not validationPlot.txName in ds_txnames:
            continue
        dataId = str(dataset.dataInfo.dataId)
        subtitle+=dataId+", "
    subtitle = subtitle[:-2]
    if hasattr ( validationPlot.expRes.globalInfo, "covariance" ):
        subtitle = "%d aggregate regions" % len(validationPlot.expRes.datasets)
    if len(subtitle) > 100:
        subtitle = subtitle[:100] + " ..."
    if len(validationPlot.expRes.datasets) == 1 and \
            type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "dataset: upper limit"

    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    if y>1e-24 and y<1e-6:
        ## assume that its a "width" axis
        plane.SetLogy()
    base.Draw("APsame")
    leg.Draw()
    #base.Draw("Psame")
    base.leg = leg
    base.SetTitle(title)
    try:
        base.GetXaxis().SetTitle(xlabel)
        base.GetYaxis().SetTitle(ylabel)
    except:
        pass
    l=TLatex()
    l.SetNDC()
    l.SetTextSize(.04)
    base.l=l
    l0=TLatex()
    l0.SetNDC()
    l0.SetTextSize(.025)
    l0.DrawLatex(.05,.905,subtitle)
    base.l0=l0
    signal_factor = 1. # an additional factor that is multiplied with the signal cross section
    agreement = 0.
    weighted = weightedAgreementFactor # compute weighted agreement factor?
    agreement = round(100.*validationPlot.computeAgreementFactor(
                       signal_factor = signal_factor, weighted = weighted ))
    logger.info ( "\033[32mAgreement: %d%s\033[0m (with %d points)" % (agreement,"%",len(validationPlot.data)) )
    if extraInfo:
        lex=TLatex()
        lex.SetNDC()
        # lex.SetTextColor( kGray )
        lex.SetTextSize(.026 )
        import socket
        hn=socket.gethostname()
        phn = hn.find(".")
        if phn > 0:
            hn = hn[:phn]
        lex.DrawLatex(.59,.12,"agreement: %d%s, t~%.1fs [%s]" % (agreement, "%", tavg, hn ) )
        base.lex=lex

    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.02)
        l1.DrawLatex(.06,.02,"%s" % figureUrl)
        base.l1=l1
    l2=TLatex()
    l2.SetNDC()
    l2.SetTextSize(.025)
    l2.SetTextAngle(90.)
    l2.SetTextColor( kGray )
    l2.DrawLatex(.93,.15,"k-factor %.2f" % kfactor)
    base.l2=l2

    l3=TLatex()
    l3.SetNDC()
    l3.SetTextSize(.025)
    l3.SetTextColor( kGray )
    dxpnr=.68 ## top, right
    if reverse: ## if reverse put this line at left of plot
        dxpnr = .12
    l3.DrawLatex( dxpnr,.87,"%d / %d points with no results" % \
                  (nErrors, len(validationPlot.data) ) )
    base.l3=l3

    if extraInfo: ## a timestamp, on the right border
        import time
        l9=TLatex()
        l9.SetNDC()
        l9.SetTextSize(.025)
        l9.SetTextAngle(90.)
        l9.SetTextColor( kGray )
        l9.DrawLatex ( .93, .65, time.strftime("%b %d, %Y, %H:%M") )
        base.l9 = l9

    if preliminary:
        ## preliminary label, ugly plot
        tprel = TLatex()
        tprel.SetNDC()
        tprel.SetTextSize(0.055)
        tprel.SetTextFont(42)
        tprel.SetTextColor ( kBlue+3 )
        tprel.SetTextAngle(-25.)
        tprel.DrawLatex(.6,.85,"SModelS preliminary")
        #tprel.SetTextAngle(25.)
        #tprel.DrawLatex(.05,.7,"SModelS preliminary")
        base.tprel = tprel

    if not silentMode:
        _ = raw_input("Hit any key to close\n")

    return plane,base

def createPrettyPlot( validationPlot,silentMode=True, preliminary=False,
                      looseness = 1.2, style = "", legendplacement = "top right" ):
    """
    Uses the data in validationPlot.data and the official exclusion curves
    in validationPlot.officialCurves to generate a pretty exclusion plot

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param preliminary: if true, write "preliminary" over the plot
    :param looseness: ?
    :param style: allow for styles, currently "", and "sabine"
    :param legendplacement: placement of legend. One of:
                      "automatic", "top right", "top left"
    :return: TCanvas object containing the plot
    """

    # Check if data has been defined:
    tgr = TGraph2D()
    kfactor=None
    xlabel, ylabel, zlabel = 'x [GeV]','y [GeV]',"r = #sigma_{signal}/#sigma_{UL}"
    logY = False
    A = validationPlot.axes.replace(" ","")
    p1 = A.find("(")
    p2 = A.find(")")
    py = A.find("y")
    #print ( "axes", A )
    if p1 < py < p2 and A[py-1]==",":
        logY = True
        xlabel = "x [mass, GeV]"
        ylabel = "y [width, GeV]"

    if not validationPlot.data:
        logger.error("Data for validation plot is not defined.")
        return (None,None)
        ## sys.exit()
    # Get excluded and allowed points:
    condV = 0
    for pt in validationPlot.data:
        #if "error" in pt.keys():
        #    continue
        if kfactor == None:
            if "kfactor" in pt.keys():
                kfactor = pt ['kfactor']
            elif not "error" in pt.keys():
                kfactor = 1.
        if (not "error" in pt.keys()) and ("kfactor" in pt.keys()) and (abs(kfactor - pt['kfactor'])> 1e-5):
            logger.error("kfactor not a constant throughout the plane!")
            sys.exit()
        #import IPython
        # IPython.embed()
        if not "axes" in pt:
            ## try to get axes from slha file
            pt["axes"] = getXYFromSLHAFile ( pt["slhafile"], validationPlot )
        xvals = pt['axes']
        if xvals == None: ## happens when not on the plane I think
            continue
        if (not "UL" in pt.keys() or pt["UL"]==None) and (not "error" in pt.keys()):
            logger.warning( "no UL for %s" % xvals )
        r = float("nan")
        if not "error" in pt.keys():
            r = pt['signal']/pt ['UL']
        if r > 3.:
            r=3.
        if isinstance(xvals,dict):
            if len(xvals) == 1:
                x,y = xvals['x'],r
                ylabel = "r = #sigma_{signal}/#sigma_{UL}"
            else:
                x = xvals["x"]
                if "y" in xvals:
                    y = xvals['y']
                elif "w" in xvals:
                    y = xvals['w']
                    
        else:
            x,y = xvals
        if logY:
            y = rescaleWidth(y)

        if "condition" in pt.keys() and pt['condition'] and pt['condition'] > 0.05:
            condV += 1
            if condV < 5:
                logger.warning("Condition violated for file " + pt['slhafile'])
            if condV == 5:
                logger.warning("Condition violated for more points (not shown)")
        else:
            if not "error" in pt.keys():
                tgr.SetPoint(tgr.GetN(), x, y, r)

    if tgr.GetN() < 4:
        logger.error("No good points for validation plot.")
        return (None,None)

    #ROOT has trouble obtaining a histogram from a 1-d graph. So it is
    #necessary to smear the points if they rest in a single line.
    if tgr.GetYmax() == tgr.GetYmin():
        logger.info("1d data detected, smearing Y values")
        tgrN = tgr.GetN()
        buff = tgr.GetX()
        buff.SetSize(tgrN)
        xpts = numpy.frombuffer(buff,count=tgrN)
        buff = tgr.GetY()
        buff.SetSize(tgrN)
        ypts = numpy.frombuffer(buff,count=tgrN)
        buff = tgr.GetZ()
        buff.SetSize(tgrN)
        zpts = numpy.frombuffer(buff,count=tgrN)
        for i in range(tgrN):
            tgr.SetPoint(i,xpts[i],ypts[i]+random.uniform(0.,0.001),zpts[i])
    if tgr.GetXmax() == tgr.GetXmin():
        logger.info("1d data detected, smearing X values")
        buff = tgr.GetX()
        buff.reshape((tgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        #print ( "count", tgr.GetN(), type(buff), buff.shape )
        xpts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetY()
        buff.reshape((tgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        ypts = numpy.frombuffer(buff,count=tgr.GetN())
        buff = tgr.GetZ()
        buff.reshape((tgr.GetN(),))
        #buff.SetSize(sys.maxsize)
        zpts = numpy.frombuffer(buff,count=tgr.GetN())
        for i in range(tgr.GetN()):
            tgr.SetPoint(i,xpts[i]+random.uniform(0.,0.001),ypts[i],zpts[i])

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        logger.debug("Official curves have length %d" % len (official) )

    if logY:
        if official is None:
            logger.error("could not find any exclusion lines for %s" % validationPlot.txName )
            official = []
        for contour in official:
            # x, y = Double(), Double()
            x, y = ctypes.c_double(), ctypes.c_double()
            n = contour.GetN()
            for i in range(n):
                contour.GetPoint(i,x,y)
                # print ( "y",y,rescaleWidth(y) )
                contour.SetPoint(i,x.value,rescaleWidth(y.value) )

    if silentMode: gROOT.SetBatch()
    setOptions(tgr, Type='allowed')
    title = validationPlot.expRes.globalInfo.id
    types = []
    for dataset in validationPlot.expRes.datasets:
        ds_txnames = map ( str, dataset.txnameList )
        if not validationPlot.txName in ds_txnames:
            continue
        types.append(dataset.dataInfo.dataType)
    types = list(set(types))
    if len(types) == 1: types = types[0]
    resultType = "%s" %str(types)
    title = title + "  #scale[0.8]{("+resultType+")}"
    tgr.SetTitle(title)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    plane.SetRightMargin(0.16)
    plane.SetTopMargin(0.16)
    plane.SetBottomMargin(0.16)
    plane.SetLeftMargin(0.12)
    gStyle.SetTitleSize(0.045,"t")
    gStyle.SetTitleY(1.005)

    #Get contour graphs:
    contVals = [1./looseness,1.,looseness]
    cgraphs = getContours(tgr,contVals)

    #Draw temp plot:
    h = tgr.GetHistogram()
    setOptions(h,Type='pretty')
    h.GetZaxis().SetRangeUser(0., min(tgr.GetZmax(),3.))
    h.GetXaxis().SetTitleFont(42)
    xa,ya = h.GetXaxis(),h.GetYaxis()
    ya.SetTitleFont(42)
    xa.SetTitleOffset(1.)
    ya.SetTitleOffset(1.2)
    xa.SetTitleSize(.04)
    ya.SetTitleSize(.04)
    xa.SetTitle(xlabel)
    ya.SetTitle(ylabel)
    h.GetZaxis().SetTitle(zlabel)
    h.SetContour(200)
    h.Draw("COLZ")
    ya = h.GetYaxis()
    if logY:
        ya.SetLabelSize(.06)
        nbins = ya.GetNbins()
        last = 0
        for i in range( 1, nbins ):
            center = ya.GetBinCenter(i)
            width = unscaleWidth ( center )
            if type(width) == type(GeV):
                width = float ( width.asNumber(GeV) )
            center10 = math.log10 ( width )
            r_center = int ( round ( center10 ) )
            delta = abs ( center10 - r_center )
            if r_center != last and delta < .1:
                ya.SetBinLabel( i, "10^{%d}" % r_center )
                last = r_center
    palette = h.GetListOfFunctions().FindObject("palette")
    palette.SetX1NDC(0.845)
    palette.SetX2NDC(0.895)
    palette.SetY1NDC(0.16)
    palette.SetY2NDC(0.84)
    for cval,grlist in cgraphs.items():
        if cval == 1.0:
            ls = 1
        else:
            ls = 2
        for gr in grlist:
            setOptions(gr, Type='official')
            gr.SetLineColor(kGray+2)
            gr.SetLineStyle(ls)
            gr.Draw("L SAME")
    if official:
        for gr in official:
            # validationPlot.completeGraph ( gr )
            setOptions(gr, Type='official')
            gr.Draw("L SAME")

    #Draw additional info
    ltx=TLatex()
    ltx.SetNDC()
    ltx.SetTextSize(.035)
    ltx.SetTextFont(42)
    ltx2 = ltx.Clone()
    ltx2.SetTextAlign(31)
    txStr = validationPlot.txName +': '+prettyTxname(validationPlot.txName,outputtype="root")
    axStr = prettyAxes(validationPlot.txName,validationPlot.axes)
    axStr = str(axStr).replace(']','').replace('[','').replace("'","")
    infoStr = "#splitline{"+txStr+'}{'+axStr+'}'
    ltx.DrawLatex(.03,.88,txStr)
    ltx2.DrawLatex(.96,.88,axStr)
    tgr.ltx = ltx
    figureUrl = getFigureUrl(validationPlot)
    if figureUrl:
        l1=TLatex()
        l1.SetNDC()
        l1.SetTextSize(.025)
        """l1.DrawLatex(.01,0.023,"#splitline{official plot:}{%s}" % figureUrl)"""
        tgr.l1=l1
    if kfactor is not None and abs ( kfactor - 1.) > .01:
        l2=TLatex()
        l2.SetNDC()
        l2.SetTextFont(132)
        l2.SetTextSize(.04)
        l2.DrawLatex(0.16,0.2,"k-factor = %.2f" % kfactor)
        tgr.l2=l2

    subtitle = "%d datasets" % len(validationPlot.expRes.datasets)
    if hasattr ( validationPlot.expRes.globalInfo, "jsonFiles" ):
        ## pyhf combination
        subtitle = "pyhf combining %d SRs" % len(validationPlot.expRes.datasets)
    dId = validationPlot.expRes.datasets[0].dataInfo.dataId
    if type(dId) == str and dId.startswith("ar"):
        subtitle = "%d aggregate datasets" % len(validationPlot.expRes.datasets)
        dataId = str(dataset.dataInfo.dataId)
    if len(validationPlot.expRes.datasets) == 1 and \
            type(validationPlot.expRes.datasets[0].dataInfo.dataId)==type(None):
        subtitle = "" ## no extra info, so leave it blank
        # subtitle = "upper limit"
    if validationPlot.combine == False and len(validationPlot.expRes.datasets) > 1:
        for ctr,x in enumerate(validationPlot.data):
            if "error" in x.keys():
                continue
            break
        if validationPlot.data != None and validationPlot.data[ctr] != None and "dataset" in validationPlot.data[ctr].keys() and validationPlot.data[ctr]["dataset"]!=None and "combined" in validationPlot.data[ctr]["dataset"]:
            logger.warning ( "asked for an efficiencyMap-type plot, but the cached validationData is for a combined plot. Will label it as 'combined'." )
        else:
            subtitle = "best SR"
    lsub=TLatex()
    lsub.SetNDC()
    if style == "sabine":
        lsub.SetTextSize(.037)
        if legendplacement == "top left": # then we move to top right with this
            lsub.DrawLatex(.57,.79,subtitle)
        else:
            lsub.DrawLatex(.15,.79,subtitle)
    else:
        lsub.SetTextAlign(31)
        # lsub.SetTextSize(.025)
        lsub.SetTextSize(.035)
        # lsub.DrawLatex(.81,.068,subtitle)
        lsub.DrawLatex(.91,.068,subtitle)
    tgr.lsub=lsub

    nleg = 1
    if cgraphs != None and official != None:
    #Count the number of entries in legend:
        nleg = min(2,len(cgraphs)-list(cgraphs.values()).count([])) + min(2,len(official))
    #Draw legend:
    dx = 0. ## top, left
    dx = .33 ## top, right
    hasExclLines = False
    # placement = "top left" ## "automatic", "top right", "top left"
    possibleplacements = [ "automatic", "auto", "top left", "top right" ]
    legendplacement = legendplacement.replace("'","")
    legendplacement = legendplacement.replace('"',"")
    legendplacement = legendplacement.lower()
    legendplacement = legendplacement.strip()
    if legendplacement not in possibleplacements:
        print ( "[plottingFuncs] ERROR placement %s not in %s" % \
                ( legendplacement, ", ".join( possibleplacements ) ) )
        sys.exit(-1)
    leg = TLegend() ## automatic placement
    if legendplacement == "top right":
        leg = TLegend(0.15+dx,0.75-0.040*nleg,0.495+dx,0.83)
    if legendplacement == "top left":
        leg = TLegend(0.15,0.75-0.040*nleg,0.495,0.83)
    setOptions(leg)
    # leg.SetFillStyle(0)
    leg.SetTextSize(0.04)
    added = False
    for cval,grlist in cgraphs.items():
        if not grlist:
            continue
        if cval == 1.0:
            leg.AddEntry(grlist[0],"exclusion (SModelS)","L")
            hasExclLines = True
        elif (cval == looseness or cval == 1./looseness) and not added:
            leg.AddEntry(grlist[0],"#pm20% (SModelS)","L")
            hasExclLines = True
            added = True
    if official != None:
        added = False
        for gr in official:
            if 'xclusion_' in gr.GetTitle():
                leg.AddEntry(gr,"exclusion (official)","L")
                hasExclLines = True
            elif ('xclusionP1_' in gr.GetTitle() or 'xclusionM1_' in gr.GetTitle()) and (not added):
                leg.AddEntry(gr,"#pm1#sigma (official)","L")
                hasExclLines = True
                added = True

    if hasExclLines:
        leg.Draw()
    tgr.leg = leg
    if preliminary:
        ## preliminary label, pretty plot
        tprel = TLatex()
        tprel.SetTextColor ( kBlue+3 )
        tprel.SetNDC()
        tprel.SetTextAngle(25.)
        tprel.SetTextSize(0.055)
        tprel.SetTextFont(42)
        tprel.DrawLatex(.1,.7,"SModelS preliminary")
        tgr.tprel = tprel
    plane.Update()

    if not silentMode:
        ans = raw_input("Hit any key to close\n")

    return plane,tgr

def createTempPlot( validationPlot, silentMode=True, what = "R", nthpoint =1,
                    signal_factor =1.):
    """
    Uses the data in validationPlot.data and the official exclusion curve
    in validationPlot.officialCurves to generate temperature plots, showing
    e.g. upper limits or R values

    :param validationPlot: ValidationPlot object
    :param silentMode: If True the plot will not be shown on the screen
    :param what: what is to be plotted ("upperlimits", "crosssections", "R")
    :param nthpoint: label only every nth point
    :param signal_factor: an additional factor that is multiplied with the signal cross section.
     Makes it easier to account for multiplicative factors, like K-factors.
    :return: TCanvas object containing the plot
    """
    kfactor=None

    grTemp = TGraph2D()
    excluded = TGraph()
    if not validationPlot.data:
        logger.warning("Data for validation plot is not defined.")
        return None
    else:
        # Get points:
        for pt in validationPlot.data:
            if kfactor == None:
                kfactor = pt['kfactor']
            if abs(kfactor - pt['kfactor'])> 1e-5:
                logger.error("kfactor not a constant throughout the plane!")
                sys.exit()

            if isinstance(pt['axes'],dict):
                if len(pt['axes']) == 1:
                    x, y = pt['axes']['x'], pt['signal']/pt['UL']
                else:
                    x, y = pt['axes']['x'],pt['axes']['y']
            else:
                x,y = pt['axes']
            pt['signal'] = pt['signal']*signal_factor
            if what == 'R':
                z = pt['signal']/pt['UL']
            elif what == 'upperlimits':
                z = pt['UL'].asNumber(pb)
            elif what == 'crosssections':
                z = pt['signal'].asNumber(pb)
            else:
                logger.error("Unknown plotting variable: %s" %what)
                return None
            grTemp.SetPoint(grTemp.GetN(),x,y,z)
            if pt['signal'] > pt['UL']:
                excluded.SetPoint(excluded.GetN(), x, y )

    zlabel = ""
    if what == "R":
        zlabel = "#sigma_{theory}/#sigma_{UL}"
    elif what == "crosssections":
        zlabel="Theory Predictions [pb]"
    elif what == "upperlimits":
        zlabel = "Upper Limits [pb]"

    # Check if official exclusion curve has been defined:
    if not validationPlot.officialCurves:
        logger.warning("Official curve for validation plot is not defined.")
        official = None
    else:
        official = validationPlot.officialCurves
        if isinstance(official,list): official = official[0]
    #Get envelopes:
    exclenvelop = TGraph(getEnvelope(excluded))
    setOptions(exclenvelop, Type='excluded')

    if silentMode: gROOT.SetBatch()
    setOptions(grTemp, Type='temperature')
    if official:
        setOptions(official, Type='official')

    base = grTemp
    title = validationPlot.expRes.globalInfo.id + "_" \
            + validationPlot.txName\
            + "_" + validationPlot.niceAxes
            # + "_" + validationPlot.axes
    figureUrl = getFigureUrl(validationPlot)
    plane = TCanvas("Validation Plot", title, 0, 0, 800, 600)
    plane.SetRightMargin(0.16)
    plane.SetLeftMargin(0.15)
    plane.SetBottomMargin(0.15)
    set_palette(gStyle)
    h = grTemp.GetHistogram()
    setOptions(h, Type='temperature')
    h.Draw("COLZ")
    h.GetZaxis().SetTitle(zlabel)
    if official:
        official.Draw("SAMEL")
    exclenvelop.Draw("SAMEL")
    base.SetTitle(title)
    if figureUrl:
        figUrl=TLatex()
        figUrl.SetNDC()
        figUrl.SetTextSize(.02)
        """figUrl.DrawLatex(.12,.1,"%s" % figureUrl)"""
        base.figUrl = figUrl
    if abs(signal_factor-1.0)>.0001:
        sigFac=TLatex()
        sigFac.SetNDC()
        sigFac.SetTextSize(.04)
        sigFac.DrawLatex(.15,.62, "signal factor %.1f" % signal_factor )
        base.sigFac = sigFac
    leg = TLegend(0.5,0.5,0.7,0.7,"")
    leg.AddEntry(official,"Official Exclusion","L")
    leg.Draw()

    plane.base = base
    plane.official = official

    if not silentMode:
        ans = raw_input("Hit any key to close\n")
    plane.Print("test.png")

    return plane


def setOptions(obj,Type=None):
    """
    Define global options for the plotting object according to its type.
    :param obj: a plotting object (TGraph, TMultiGraph, TCanvas,...)
    :param type: a string defining the object (allowed, excluded, official,...)
    """

    #Defaul settings:
    if isinstance(obj,TCanvas):
        obj.SetLeftMargin(0.1097891)
        obj.SetRightMargin(0.02700422)
        obj.SetTopMargin(0.02796053)
        obj.SetBottomMargin(0.14796053)
        obj.SetFillColor(0)
        obj.SetBorderSize(0)
        obj.SetFrameBorderMode(0)
    elif isinstance(obj,TGraph):
        obj.GetYaxis().SetTitleFont(132)
        obj.GetYaxis().SetTitleSize(0.075)
        obj.GetYaxis().CenterTitle(True)
        obj.GetYaxis().SetTitleOffset(1.15)
        obj.GetXaxis().SetTitleFont(132)
        obj.GetXaxis().SetTitleSize(0.075)
        obj.GetXaxis().CenterTitle(True)
        obj.GetXaxis().SetTitleOffset(1.2)
        obj.GetYaxis().SetLabelFont(132)
        obj.GetXaxis().SetLabelFont(132)
        obj.GetYaxis().SetLabelSize(0.055)
        obj.GetXaxis().SetLabelSize(0.06)
    elif isinstance(obj,TLegend):
        obj.SetBorderSize(1)
        obj.SetMargin(0.35)
        obj.SetTextFont(132)
        obj.SetTextSize(0.05)
        obj.SetLineColor(kBlack)
        obj.SetLineStyle(1)
        obj.SetLineWidth(1)
        obj.SetFillColorAlpha(kWhite,.7)
        obj.SetFillStyle(1001)
    elif isinstance(obj,TGraph2D) or isinstance(obj,TH2D):
        obj.GetZaxis().SetTitleFont(132)
        obj.GetZaxis().SetTitleSize(0.06)
        obj.GetZaxis().CenterTitle(True)
        obj.GetZaxis().SetTitleOffset(0.7)
        obj.GetZaxis().SetLabelFont(132)
        obj.GetZaxis().SetLabelSize(0.05)
        obj.GetYaxis().SetTitleFont(132)
        obj.GetYaxis().SetTitleSize(0.075)
        obj.GetYaxis().CenterTitle(True)
        obj.GetYaxis().SetTitleOffset(1.15)
        obj.GetXaxis().SetTitleFont(132)
        obj.GetXaxis().SetTitleSize(0.075)
        obj.GetXaxis().CenterTitle(True)
        obj.GetXaxis().SetTitleOffset(1.2)
        obj.GetYaxis().SetLabelFont(132)
        obj.GetXaxis().SetLabelFont(132)
        obj.GetYaxis().SetLabelSize(0.055)
        obj.GetXaxis().SetLabelSize(0.06)

#Type-specific settings:
    if not Type: return True
    elif Type == 'allowed':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kGreen)
    elif Type == 'gridpoints':
        obj.SetMarkerStyle(28)
        markersize=.1 ## super small for > 155555
        ngpoints = obj.GetN()
        if ngpoints < 1500:
            markersize = .15
        if ngpoints < 1000:
            markersize = .25
        if ngpoints < 500:
            markersize = .45
        if ngpoints < 150:
            markersize = .7
        if ngpoints < 50:
            markersize = .9
        obj.SetMarkerSize(markersize)
        obj.SetMarkerColorAlpha(kBlue,.5)
    elif Type == 'noresult':
        obj.SetMarkerStyle(20)
        obj.SetMarkerSize(.5)
        obj.SetMarkerColor(kGray)
    elif Type == 'cond_violated':
        obj.SetMarkerStyle(23)
        obj.SetMarkerColor(kGreen)
    elif Type == 'excluded':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kRed)
#        obj.SetFillColorAlpha(kRed,0.15)
        obj.SetLineColor(kRed)
        obj.SetLineWidth(4)
        obj.SetLineStyle(2)
    elif Type == 'allowed_border':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kGreen+3)
    elif Type == 'excluded_border':
        obj.SetMarkerStyle(20)
        obj.SetMarkerColor(kOrange+1)
    elif Type == 'official':
        obj.SetLineWidth(3)
        obj.SetLineColor(kBlack)
    elif Type == 'smodels':
        obj.SetLineWidth(4)
        obj.SetLineColor(kRed)
    elif Type == 'temperature':
        obj.SetMarkerStyle(20)
        obj.SetMarkerSize(1.5)
        obj.SetTitle("")
    elif Type == 'pretty':
        obj.GetXaxis().SetTitleFont(12)
        obj.GetXaxis().SetTitleOffset(0.7)
        obj.GetYaxis().SetTitleFont(12)
        obj.GetYaxis().SetTitleOffset(0.8)
        obj.GetZaxis().CenterTitle()
        obj.GetZaxis().SetTitleOffset(1.05)
        obj.GetXaxis().SetLabelSize(0.045)
        obj.GetYaxis().SetLabelSize(0.045)
        obj.GetZaxis().SetLabelSize(0.04)
        obj.GetXaxis().SetTitleSize(0.06)
        obj.GetYaxis().SetTitleSize(0.06)
        obj.GetZaxis().SetTitleSize(0.051)


def getContours(tgr,contVals):
    """
    Returns a list of TGraphs containing the curves corresponding to the
    contour values contVals from the input TGraph2D object
    :param tgr: ROOT TGraph2D object containing the x,y,r points
    :param contVals: r-values for the contour graphs

    :return: a dictionary, where the keys are the contour values
             and the values are a list of TGraph objects containing the curves
             for the respective contour value (e.g. {1. : [TGraph1,TGraph2],...})
    """

    if tgr.GetN() == 0:
        logger.info("No excluded points found for %s" %tgr.GetName())
        return None

    cVals = sorted(contVals)
    if tgr.GetN() < 4:
        print ( "Error: Cannot create a contour with fewer than 3 input vertices" )
        return None
    h = tgr.GetHistogram()
    #Get contour graphs:
    c1 = TCanvas()
    h.SetContour(3,array('d',cVals))
    h.Draw("CONT Z LIST")
    c1.Update()
    clist = gROOT.GetListOfSpecials().FindObject("contours")
    cgraphs = {}
    for i in range(clist.GetSize()):
        contLevel = clist.At(i)
        curv = contLevel.First()
        cgraphs[cVals[i]] = []
        for j in range(contLevel.GetSize()):
            cgraphs[cVals[i]].append(curv)
            curv = contLevel.After(curv)

    return cgraphs

def getEnvelope(excludedGraph):
    """
    Tries to return the envelope curve of the points in the
    excluded graph (ROOT TGraph).
    :param excludedGraph: ROOT TGraph object containing the excluded points.
    :return: a TGraph object containing the envelope curve
    """
    if excludedGraph.GetN() == 0:
        logger.info("No excluded points found for %s" %excludedGraph.GetName())
        return excludedGraph

    envelop = TGraph()
    envelop.SetName("envelope")
    curve = TGraph(excludedGraph)
    curve.Sort()
    # x1, y1 = Double(), Double()
    x1, y1 = ctypes.c_double(), ctypes.c_double()
    curve.GetPoint(0, x1, y1)
    yline = []
    for ipt in range(curve.GetN() + 1):
        # x, y = Double(), Double()
        x, y = ctypes.c_double(), ctypes.c_double()
        dmin = 0.
        if ipt < curve.GetN(): curve.GetPoint(ipt, x, y)
        if ipt != curve.GetN() and x == x1: yline.append(y)
        else:
            yline = sorted(yline, reverse = True)
            dy = [abs(yline[i] - yline[i + 1]) for i in range(len(yline) - 1)]
            if len(yline) <= 3 or envelop.GetN() == 0:
                newy = max(yline)
                if len(dy) > 2: dmin = min([abs(yline[i] - yline[i + 1]) for i in range(len(yline) - 1)])
            else:
                newy = max(yline)
        #        dmin = min(dy)
                dmin = sum(dy) / float(len(dy))
                for iD in range(len(dy) - 1):
                    if dy[iD] <= dmin and dy[iD + 1] <= dmin:
                        newy = yline[iD]
                        break
            envelop.SetPoint(envelop.GetN(), x1, newy + dmin/2.)
            x1 = x
            yline = [y]

    # x2, y2 = Double(), Double()
    x2, y2 = ctypes.c_double(), ctypes.c_double()
    envelop.GetPoint(envelop.GetN() - 1, x2, y2)
    envelop.SetPoint(envelop.GetN(), x2, 0.)  #Close exclusion curve at zero
    return envelop

def set_palette(gStyle, ncontours=999):
    """Set a color palette from a given RGB list
    stops, red, green and blue should all be lists of the same length
    see set_decent_colors for an example"""

    # default palette, looks cool
    stops = [0.00, 0.34, 0.61, 0.84, 1.00]
    red   = [0.00, 0.00, 0.87, 1.00, 0.51]
    green = [0.00, 0.81, 1.00, 0.20, 0.00]
    blue  = [0.51, 1.00, 0.12, 0.00, 0.00]

    s = array('d', stops)
    r = array('d', red)
    g = array('d', green)
    b = array('d', blue)

    npoints = len(s)
    TColor.CreateGradientColorTable(npoints, s, r, g, b, ncontours)
    gStyle.SetNumberContours(ncontours)

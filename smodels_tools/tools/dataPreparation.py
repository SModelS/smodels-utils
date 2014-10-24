import ROOT, sys, math, copy
from array import array

ROOT.gROOT.ProcessLine(".L /afs/hephy.at/user/w/walten/public/sms/scripts/useNiceColorPalette.C")
sys.path.append ( "/afs/hephy.at/user/w/walten/public/sms/scripts" )

#from Experiment.SMSHelpers import getCanonicalName

def getDataFromNames(path):
    """read the names.txt file and return the infos as nested dictionary
    :param:path: absolute path of the analysis
    :return: {extendedtopolgy:{'limit': fileName with limitHisto, 'exclusion': fileName with exclusionline,...}}
    inner dictionary is only extended with key, if there are datas for this keyword in names.txt
    fileName is allways a absolute path inkluding the the name of
    the coresponding Object
    
    """
    f = open(path+'/orig/names.txt','r')
    lines = f.readlines()
    data = {}
    defoults = ['link','file','comment']
    for l in lines:
        if l[:1] == 'T':
            l= l.split()
            topo = l[0]
            data[topo] = {}
            if len(l) == 2:
                if l[1] == "on/off": data[topo]["split"] = True
            continue
        if not l.split()==[] and  not 'Fig' in l and not 'fig' in l:
            obj = l.split()[0]
            print 
            fileName = l.split()[1] 
            if not fileName in defoults: 
                data[topo][obj] = path+'/orig/'+fileName
    f.close
    return data
    
def getObject(path):
    """return the object storred in root-Makro (.C) or root-file (.root)
    :param: path: absolute path to the file plus objectName e.g: "path/objectName"
    
    """
    
    pathList = path.split("/")
    filePath = [directory + "/" for directory in pathList[:-1]]
    filePath = ''.join(filePath)[:-1]
    objName = pathList[-1]
    if ".root" in path:
        f = ROOT.TFile(filePath)
        obj = f.Get(objName)
        if not isinstance(obj,ROOT.TGraph):
            obj.SetDirectory(0)
        f.Close()
        return obj
    if ".C" in path:
        ROOT.gROOT.ProcessLine(".x "+filePath)
        obj = eval("ROOT."+objName)
        return obj


def getCanonicalName ( topo ):
    """ define a canonical name: w and z's are uppercase letters, etc """
    topo=topo.replace("w","W").replace("z","Z" )
    return topo

def txtFileToPythonDict ( Filename, xyReverse=False, infb=False ):
    """ turn a text file into a python dictionary containing the upper
            limits as a function of the particle masses """
    ret={}
    f=open(Filename)
    lines=f.readlines()
    f.close()
    for line in lines:
        if line.find("#")>-1:
          line=line[:line.find("#")]
        try:
            tokens=map(float,line.split())
            if len(tokens)<3:
                continue
            mx,my,ul=tokens
            if xyReverse: mx,my=my,mx
            if not ret.has_key ( mx ): ret[mx]={}
            if infb: ul=ul/1000
            ret[mx][my]=ul
        except Exception,e:
            print "[Standardizer.py] exception",e
    print ret
    return ret

dictionaries={}
expecteddict={}

def saveAsPythonDict ( topo, Filename, xyReverse=False, infb=False ):
    """ keep the upper limit dictionary in <dictionaries>,
            so that later we can make it persistent """
    Dict=txtFileToPythonDict ( Filename, xyReverse, infb )
    dictionaries[getCanonicalName(topo)]=Dict

def saveHistAsPythonDict ( hist, topo, expected=False, infb=False ):
    Dict={}
    for x in range(1, hist.GetXaxis().GetNbins()+1):
        mx = hist.GetXaxis().GetBinCenter(x)
        if not Dict.has_key( mx ): Dict[mx]={}
        for y in range(1, hist.GetYaxis().GetNbins()+1):
            my = hist.GetYaxis().GetBinCenter(y)
            ul = hist.GetBinContent(x, y)
            if ul == 0.: continue
            if infb: ul=ul/1000
            Dict[mx][my]=ul
    if expected:
        expecteddict[getCanonicalName(topo)]=Dict
    else:
        dictionaries[getCanonicalName(topo)]=Dict

def makeDicts():
    if len ( dictionaries) == 0 and len( expecteddict ) == 0: return
    f=open("sms.py","w")
    if len ( dictionaries) != 0:
        f.write ( "Dict={}\n"    )
        for (key,value) in dictionaries.items():
            f.write ( "Dict['%s']=%s\n" % ( key, value) )
    if len ( expecteddict) != 0:
        f.write ( "ExpectedDict={}\n"    )
        for (key,value) in expecteddict.items():
            f.write ( "ExpectedDict['%s']=%s\n" % ( key, value) )
    f.close()

def fail( xs, xsLimit):
    return xsLimit>1 or not xsLimit

def deltax ( histo ):
    """ do I have to rebin? If so, by how much? """
    x=histo.GetXaxis()
    xmin=x.GetXmin()
    binwidth=x.GetBinWidth(1)

    delta=0.
    if math.fabs ( math.fmod ( xmin, binwidth ) ) < 3.:
        delta=binwidth/2. ## 12.5
    #print "[deltax] xmin=",xmin,"binwidth=",binwidth,"delta=",delta
    return delta

def deltay ( histo ):
    """ do I have to rebin? If so, by how much? """
    x=histo.GetYaxis()
    xmin=x.GetXmin()
    binwidth=x.GetBinWidth(1)

    delta=0.
    if math.fabs ( math.fmod ( xmin, binwidth ) ) < 3.:
        delta=binwidth/2. ## 12.5
    #print "[deltay] ymin=",xmin,"binwidth=",binwidth,"delta=",delta
    return delta

def rebin ( histo ):
    dltx=deltax(histo)
    hx=histo.GetXaxis()
    #print "[Standardizer.py] xmin=",hx.GetXmin(),", xmax=",hx.GetXmax()," width=",hx.GetBinWidth(1)," rebin by",dltx
#    xmin=hx.GetXmin()-dltx
#    xmax=hx.GetXmax()-dltx
    xmin=hx.GetBinLowEdge(hx.GetFirst())
    xmax=hx.GetBinUpEdge(hx.GetLast())
    nx=hx.GetLast()-hx.GetFirst()+1
#    nx=hx.GetNbins()
    #delta_x = hx.GetBinWidth(1)
    hy=histo.GetYaxis()
    dlty=deltay(histo)
    #print "[Standardizer.py] ymin=",hy.GetXmin(),", rebin by",dlty
#    ymin=hy.GetXmin()-dlty
#    ymax=hy.GetXmax()-dlty
    ymin=hy.GetBinLowEdge(hy.GetFirst())
    ymax=hy.GetBinUpEdge(hy.GetLast())
    ny=hy.GetLast()-hy.GetFirst()+1
#    ny=hy.GetNbins()
    # delta_y = hy.GetBinWidth(1)
    newh=ROOT.TH2F ( histo.GetName(), histo.GetTitle(), \
            nx, xmin, xmax, ny, ymin, ymax )
    i=1
    j=1
    for bx in range(hx.GetFirst(),hx.GetLast()+1):
        for by in range(hy.GetFirst(),hy.GetLast()+1):
            c=histo.GetBinContent(bx,by)
            #mGL=hx.GetBinCenter(bx)
            #mLSP=hx.GetBinCenter(by)
            newh.SetBinContent(i,j,c)
            j+=1
        j=1
        i+=1
    return newh

def swapAxesGraph ( graph ):
    """ swap the x- and y- axes for a graph """
    rx,ry=ROOT.Double(0.),ROOT.Double(0.)
    n=graph.GetN()
    for i in range(n):
        graph.GetPoint(i,rx,ry)
        x=float(rx)
        y=float(ry)
        graph.SetPoint(i,ry,rx)
    return graph

def swapAxes ( histo ):
    """ swap the x- and the y axis """
    dltx=deltax(histo)
    dltx=0.
    hx=histo.GetXaxis()
    xmin=hx.GetXmin()-dltx
    xmax=hx.GetXmax()-dltx
    nx=hx.GetNbins()
    hy=histo.GetYaxis()
    dlty=deltay(histo)
    dlty=0.
    ymin=hy.GetXmin()-dlty
    ymax=hy.GetXmax()-dlty
    ny=hy.GetNbins()

    newh=ROOT.TH2F ( histo.GetName(), histo.GetTitle(), \
            ny, ymin, ymax, nx, xmin, xmax )
    for bx in range(nx+1):
        for by in range(ny+1):
            c=histo.GetBinContent(bx,by)
            #mGL=hx.GetBinCenter(bx)
            #mLSP=hx.GetBinCenter(by)
            newh.SetBinContent(by,bx,c)
    return newh

def axisLabels ( topo, tev=7 ):
    xparticle=productionMode ( topo, tev )
    xlabel="%s mass [GeV]" % ( xparticle )
    ylabel="LSP mass [GeV]"
    return { "x": xlabel, "y": ylabel }

def init():
    ROOT.gROOT.SetBatch()
    ROOT.gROOT.SetStyle("Plain")
    ROOT.gStyle.SetOptStat(0000)
    ROOT.gStyle.SetCanvasDefH(400)
    ROOT.gStyle.SetCanvasDefW(400)
    ROOT.gStyle.SetTitleY(0.885)
    ROOT.gStyle.SetPadTickX(1)
    ROOT.gStyle.SetPadTickY(1)
    ROOT.gStyle.SetPadBottomMargin(0.14)
    ROOT.gStyle.SetPadTopMargin(0.1)
    ROOT.gStyle.SetPadRightMargin(0.2)
    ROOT.gStyle.SetPadLeftMargin(0.15)
    ROOT.gStyle.SetPalette(1)
    ROOT.gStyle.SetTitleYOffset(1.8)
    ROOT.gStyle.SetTitleXOffset(1.1)
    ROOT.useNiceColorPalette()

def limitHisto ( hold, topo, expected=False, plusminussigma=0, infb=False, tev=7 ):
    """ standardize a limit histo plot """
    init()
    topo=getCanonicalName ( topo )
    histo=rebin ( hold )
    topo=getCanonicalName ( topo )
    axes=axisLabels ( topo, tev )
    histo.SetXTitle ( axes["x"] )
    histo.SetYTitle ( axes["y"] )
    histo.SetZTitle ( "95% CL upper limit on #sigma [pb] (CL_{s})" )
    pm1=""
    if plusminussigma==1: pm1="p1"
    if plusminussigma==-1: pm1="m1"
    name="limit%s_%s" % (pm1, topo    )
    if expected:
        name="expected"+name
    histo.SetName( name )
    histo.SetTitle( name )
    if infb:
        histo.Scale(1./1000.)
    return histo
    
def limitHistoFromTxt(  topo, fileName, expected=False, plusminussigma=0, infb=False, tev=7 ):
    """bild a limitHisto-rootplt out from txt file
    
    """
    
    txtFile = open(fileName,'r')
    xList = []
    yList = []
    limitList = []
    for line in txtFile.readlines():
        x,y,limit = line.split()
        xList.append(float(x))
        yList.append(float(y))
        limitList.append(float(limit))
    xAxes = []
    yAxes = []
    for x in xList:
        if not x in xAxes: xAxes.append(x)
    for y in yList:
        if not y in yAxes: yAxes.append(y)
    xAxes.sort()
    yAxes.sort()
    print 'xAxes: %s' %xAxes
    print 'yAxes: %s' %yAxes
    deltaX = xAxes[0]-xAxes[1]
    deltaY = yAxes[0]-yAxes[1]
    xmin = min(xAxes)-deltaX/2
    xmax = max(xAxes)+deltaX/2
    ymin = min(yAxes)-deltaY/2
    ymax = max(yAxes)+deltaY/2
    histo = ROOT.TH2F('topo' ,'topo' ,len(xAxes) ,xmin ,xmax , len(yAxes), ymin, ymax)
    for i,value in enumerate(xList):
        histo.Fill(xList[i],yList[i],limitList[i])
    histo = limitHisto( histo, topo, expected, plusminussigma, infb, tev )
    return histo
    
        

def bestSelectionHisto ( hold, topo ):
    """ standardize a limit histo plot """
    topo=getCanonicalName ( topo )
    init()
    histo=rebin ( hold )
    axes=axisLabels ( topo )
    histo.SetXTitle ( axes["x"] )
    histo.SetYTitle ( axes["y"] )
    histo.SetZTitle ( "best selection" )
    histo.SetName("bestsel_%s" % topo )
    histo.SetTitle("bestsel_%s" % topo )
    return histo

def productionMode ( process, tev=7 ):
    """ the production mode of a process. E.g T1 -> gluino """
    process=getCanonicalName ( process )
    if process=="T2tt":
        return "stop%dTeV_NLONLL" % tev
    if process[:6]=="T6bbWW":
        return "stop%dTeV_NLONLL" % tev
    if process[:6]=="T6ttWW":
        return "sbottom%dTeV_NLONLL" % tev
    if process=="T2bb":
        return "sbottom%dTeV_NLONLL" % tev
    if process=="TChiZZ":
        return "neutralino%dTeV_NLO" % tev
    if tev==8 and process in [ "TChiWZ", "TChiNuSlep", "TChiSlepSlep", "TChiSlep", "TChiZW" ]:
        return "c1n2_8TeV_NLO"
    if [ "TChiNuSlep", "TChiSlepSlep", "TChiSlep", "TChiZW", "TChiWZ" ].count ( process ):
        return "chargino%dTeV_NLO" % tev
    if process in [ "T2ttWW" ]:
        return "sbottom%dTeV_NLONLL" % tev
    if process[:2]=="T2":
        return "squark%dTeV_NLONLL" % tev
    return "gluino%dTeV_NLONLL" % tev

def getHisto( filename, histoName, dirName, nBin, lumi):
    file0 = ROOT.TFile.Open(filename)
    if not file0: return None
    hMuPt=None
    hpt_=None
    if dirName == "0":
        hMuPt = file0.Get(histoName)
    else:
        dir = file0.Get(dirName)
        if not dir: return None
        hMuPt = dir.Get(histoName)

    if(hMuPt):
        hpt_ = hMuPt.Clone()
        hpt_.Sumw2()
        hpt_.Scale(1./lumi) # this take into into account the luminosity
        hpt_.SetLineWidth(2)
        # need to comment for the acceptance since I do only one smearing
        # hpt_.Scale(0.01); // this to count the multi-smearing
        hpt_.Rebin(nBin)
        nBinX=hpt_.GetNbinsX()
        hpt_.SetBinContent(nBinX,hpt_.GetBinContent(nBinX)+hpt_.GetBinContent(nBinX+1))

        hpt_.SetDirectory(0)
        file0.Close()

        hpt_.SetLineWidth(3)

#        H = ROOT.TH1D("H", "H", 85, 300, 2000)
#        newbin=0
#
#        for i in range(1,nBinX+1):
#         if i%2: newbin+=1
#         H.Fill(i, hpt_.GetBinContent(i))
    return hpt_

def produceReferenceXSecGraphOld ( limit, topo, refMult, uptoDiagonal=True, \
        glmin=0., deltamin=0., debug="", minyvalue=0. ):
    """ produce the exclusion lines """
    topo=getCanonicalName ( topo )
    pointsX,pointsY=[],[]
    pmode=productionMode ( topo )+"7TeV_NLONLL"
    rootfile="/afs/hephy.at/user/w/walten/public/referenceXSecs.root"
    hRef=getHisto(rootfile, pmode, "0", 1,1)
    if hRef==None:
        print "[Standardizer::getRefXsecGraph] I got no hRef. rootfile=",rootfile,"mass=",mass
        sys.exit(0)
    ## print "[SMSPlotter::getRefXsecGraph] productiom mode",pmode
    limit_ref = limit.Clone()

    xmmin=limit_ref.GetXaxis().GetXmin()
    xmmax=limit_ref.GetXaxis().GetXmax()
    xmn=limit_ref.GetXaxis().GetNbins()
    ymmin=limit_ref.GetYaxis().GetXmin()
    ymmax=limit_ref.GetYaxis().GetXmax()
    ymn=limit_ref.GetYaxis().GetNbins()

    xSec_ref= ROOT.TH2F("xSec_ref","xSec_ref",xmn, xmmin, xmmax, ymn, ymmin, ymmax)

    factors = { "T2":4./5, "T2bb":1./5 }

    for i in range(1,limit.GetNbinsX()+1):
        for j in range(1,limit.GetNbinsY()+1):
            if limit.GetBinContent(i,j)==0:
                continue
            factor=1.0
            if factors.has_key ( pmode ):
                factor=factors[pmode]
            prev=hRef.GetBinContent(hRef.FindBin(xSec_ref.GetXaxis().GetBinCenter(i)) )
            xSec_ref.SetBinContent(i,j,refMult*factor*prev)
            mgl=limit.GetBinCenter(i)
            mlsp=limit.GetBinCenter(j)
            for ddb in debug:
                if ddb.has_key("mgl") and ddb.has_key("mlsp") and \
                     math.fabs ( mgl - ddb["mgl"] ) < 20 and \
                    math.fabs ( mlsp - ddb["mlsp"] ) < 20:
                    print "[SMSPlotter] debug point: mgl=%.1f mlsp=%.1f refMult=%.1f refXSec=%.5f ul=%.5f" \
                                % ( mgl, mlsp, refMult, refMult*factor*prev, limit_ref.GetBinContent(i,j) )

    limit_ref.Divide(xSec_ref)

    xSec_ref.SetDirectory(0)

    #xSec_ref.Delete()
    #hRef.Delete()
    foundDiag=False
    #tabletitles=[ "lsp" ]
    #for i in range (1,10):
    #    tabletitles.append ( str ( limit_ref.GetXaxis().GetBinCenter(i) ) )
    #p=prettytable.PrettyTable(tabletitles)

    enough = False
    for i in range (1,limit_ref.GetNbinsX()+1):
        for j in range (1,limit_ref.GetNbinsY()+1):
            added=False
            if limit_ref.GetBinContent(i,j)>0. and limit_ref.GetBinContent(i,j)<=1.:
                xsLimitAbove = limit_ref.GetBinContent(i, j+1)
                xsLimit = limit_ref.GetBinContent(i, j)
                ## if True:
                if fail(1.0,xsLimitAbove) and not fail(1.0,xsLimit):
                ##    if ( math.fabs ( refMult - 1.0 ) ) < 0.1:
                ##        print "adding a point!"
                    added=True
                    pointsX.append ( limit_ref.GetXaxis().GetBinCenter(i) )
                    pointsY.append ( limit_ref.GetYaxis().GetBinCenter(j) )
                    enough = ( math.fabs ( xsLimitAbove ) < 1e-5 )
                    ## print "xsLimitAbove=",xsLimitAbove,"enough=",enough

                    if not enough and not foundDiag: foundDiag=len(pointsX)
    #        if (    limit_ref.GetXaxis().GetBinCenter(i) < 600. and limit_ref.GetBinContent(i,j) > 0. and refMult == 1. ):
    #            print "[SMSPlotter] x=%d    y=%d    s=%.1f add %d" \
    #                % ( limit_ref.GetXaxis().GetBinCenter(i),\
    #                        limit_ref.GetYaxis().GetBinCenter(j),
    #                        limit_ref.GetBinContent(i,j), added )
        # p.add_row ( row )
    ## p.printt()
    ## print "[getRefXsecGraph] enough %d foundDiag %d" % ( enough, foundDiag )

    if len(pointsX)>1:
        pointsX.append ( pointsX[-1] )
        pointsY.append ( minyvalue )

    #if refMult==1.:
    #    for (ctr,i) in enumerate(pointsX):
    #        print "[SMSPlotter] x=%d y=%d" % ( pointsX[ctr], pointsY[ctr] )


    tempGraph = ROOT.TCanvas()
    tempGraph.cd()

    limit_ref.SetMaximum(1)
    ROOT.gStyle.SetNumberContours( 1 )
    limit_ref.Draw("cont")
    ROOT.gStyle.SetNumberContours( 20 )

    titleGraph = "graph_%s_%f.pdf" % ( limit_ref.GetName(),refMult)
    if False:
        tempGraph.SaveAs(titleGraph)
    newPointsX,newPointsY=[],[]

    for ix in range( len(pointsX) ):
        if uptoDiagonal and ix<(foundDiag-2): continue
        if ix!=len(pointsX)-1 and pointsX[ix+1]==pointsX[ix]: continue
        if pointsX[ix]<glmin: continue
        if pointsX[ix]-pointsY[ix]<deltamin: continue

        newPointsX.append ( pointsX[ix] )
        newPointsY.append ( pointsY[ix] )

    titleHisto="graph_%s_%f" % ( limit_ref.GetName(),refMult )
    if len(newPointsX)==0:
        #print "[SMSPlotter] warning: no limit for",titleHisto
        #print "[SMSPlotter] I have no new points, but ",len(pointsX),"old points"
        return None
    gr = ROOT.TGraph(len(newPointsX),array('f',newPointsX),\
                                                                     array('f',newPointsY) )
    gr.SetName(titleHisto)
    gr.Draw("same")
    return gr

def produceReferenceXSecGraph ( limit, topo, refMult=1., uptoDiagonal=True, \
        glmin=0., deltamin=0., debug="", minyvalue=0., plusminussigma=0, tev=7 ):
    """ produce the exclusion lines """
    pointsX,pointsY=[],[]
    topo=getCanonicalName ( topo )
    pmode=productionMode ( topo, tev )
    print "pmode=",pmode
    ##pmode="gluino_NLONLL"
    rootfile="/afs/hephy.at/user/w/walten/public/referenceXSecs.root"
    hRef=getHisto(rootfile, pmode, "0", 1,1)
    if plusminussigma!=0:
        hAdd=getHisto(rootfile, pmode+"_unc", "0", 1,1 ).Clone()
        hRef.Add ( hAdd, float(plusminussigma) )
    print "debug hRef=",hRef,"pmode=",pmode
    spline=ROOT.TSpline3(hRef)
    if hRef==None:
        print "[Standardizer::getRefXsecGraph] I got no hRef. rootfile=",rootfile,"mass=",mass
        sys.exit(0)
    print "[SMSPlotter::getRefXsecGraph] productiom mode",pmode
    limit_ref = limit.Clone()

    xmmin=limit_ref.GetXaxis().GetXmin()
    xmmax=limit_ref.GetXaxis().GetXmax()
    xmn=limit_ref.GetXaxis().GetNbins()
    ymmin=limit_ref.GetYaxis().GetXmin()
    ymmax=limit_ref.GetYaxis().GetXmax()
    ymn=limit_ref.GetYaxis().GetNbins()

    xSec_ref= ROOT.TH2F("xSec_ref","xSec_ref",xmn, xmmin, xmmax, ymn, ymmin, ymmax)

    factors = { "T2":4./5, "T2bb":1./5 }

    for i in range(1,limit.GetNbinsX()+1):
        for j in range(1,limit.GetNbinsY()+1):
            if limit.GetBinContent(i,j)==0:
                continue
            factor=1.0
            if factors.has_key ( pmode ):
                factor=factors[pmode]
            mgl=limit.GetBinCenter(i)
            mlsp=limit.GetBinCenter(j)
            prev=spline.Eval(mgl)
            # prev=hRef.GetBinContent(hRef.FindBin(xSec_ref.GetXaxis().GetBinCenter(i)) )
            xSec_ref.SetBinContent(i,j,refMult*factor*prev)
            ## spline->Eval(mgl)
            for ddb in debug:
                if ddb.has_key("mgl") and ddb.has_key("mlsp") and \
                     math.fabs ( mgl - ddb["mgl"] ) < 20 and \
                    math.fabs ( mlsp - ddb["mlsp"] ) < 20:
                    print "[SMSPlotter] debug point: mgl=%.1f mlsp=%.1f refMult=%.1f refXSec=%.5f ul=%.5f" \
                                % ( mgl, mlsp, refMult, refMult*factor*prev, limit_ref.GetBinContent(i,j) )

    limit_ref.Divide(xSec_ref)

    xSec_ref.SetDirectory(0)

    #xSec_ref.Delete()
    #hRef.Delete()
    foundDiag=False
    #tabletitles=[ "lsp" ]
    #for i in range (1,10):
    #    tabletitles.append ( str ( limit_ref.GetXaxis().GetBinCenter(i) ) )
    #p=prettytable.PrettyTable(tabletitles)

    enough = False
    for i in range (1,limit_ref.GetNbinsX()+1):
        for j in range (1,limit_ref.GetNbinsY()+1):
            added=False
            if limit_ref.GetBinContent(i,j)>0. and limit_ref.GetBinContent(i,j)<=1.:
                xsLimitAbove = limit_ref.GetBinContent(i, j+1)
                xsLimit = limit_ref.GetBinContent(i, j)
                ## if True:
                if fail(1.0,xsLimitAbove) and not fail(1.0,xsLimit):
                ##    if ( math.fabs ( refMult - 1.0 ) ) < 0.1:
                ##        print "adding a point!"
                    added=True
                    pointsX.append ( limit_ref.GetXaxis().GetBinCenter(i) )
                    pointsY.append ( limit_ref.GetYaxis().GetBinCenter(j) )
                    enough = ( math.fabs ( xsLimitAbove ) < 1e-5 )
                    ## print "xsLimitAbove=",xsLimitAbove,"enough=",enough

                    if not enough and not foundDiag: foundDiag=len(pointsX)
    #        if (    limit_ref.GetXaxis().GetBinCenter(i) < 600. and limit_ref.GetBinContent(i,j) > 0. and refMult == 1. ):
    #            print "[SMSPlotter] x=%d    y=%d    s=%.1f add %d" \
    #                % ( limit_ref.GetXaxis().GetBinCenter(i),\
    #                        limit_ref.GetYaxis().GetBinCenter(j),
    #                        limit_ref.GetBinContent(i,j), added )
        # p.add_row ( row )
    ## p.printt()
    ## print "[getRefXsecGraph] enough %d foundDiag %d" % ( enough, foundDiag )

    if len(pointsX)>1:
        pointsX.append ( pointsX[-1] )
        pointsY.append ( minyvalue )

    #if refMult==1.:
    #    for (ctr,i) in enumerate(pointsX):
    #        print "[SMSPlotter] x=%d y=%d" % ( pointsX[ctr], pointsY[ctr] )


    tempGraph = ROOT.TCanvas()
    tempGraph.cd()

    limit_ref.SetMaximum(1)
    ROOT.gStyle.SetNumberContours( 1 )
    limit_ref.Draw("cont")
    ROOT.gStyle.SetNumberContours( 20 )

    titleGraph = "graph_%s_%f.pdf" % ( limit_ref.GetName(),refMult)
    if False:
        tempGraph.SaveAs(titleGraph)
    newPointsX,newPointsY=[],[]

    for ix in range( len(pointsX) ):
        if uptoDiagonal and ix<(foundDiag-2): continue
        if ix!=len(pointsX)-1 and pointsX[ix+1]==pointsX[ix]: continue
        if pointsX[ix]<glmin: continue
        if pointsX[ix]-pointsY[ix]<deltamin: continue

        newPointsX.append ( pointsX[ix] )
        newPointsY.append ( pointsY[ix] )

    #titleHisto="graph_%s_%f" % ( limit_ref.GetName(),refMult )
    titleHisto="exclusion_%s" % topo
    if abs ( refMult - 3. ) < 1e-5:
        titleHisto="exclusion3_%s" % topo
    if abs ( refMult - 1./3. ) < 1e-5:
        titleHisto="exclusion13_%s" % topo
    if len(newPointsX)==0:
        #print "[SMSPlotter] warning: no limit for",titleHisto
        #print "[SMSPlotter] I have no new points, but ",len(pointsX),"old points"
        return None
    gr = ROOT.TGraph(len(newPointsX),array('f',newPointsX),\
                                                                     array('f',newPointsY) )
    gr.SetName(titleHisto)
    gr.SetTitle(titleHisto)
    gr.Draw("same")
    return gr

def effHisto ( hold, topo, percent=False, tev=7 ):
    """ standardize an efficiency histo plot """
    topo=getCanonicalName ( topo )
    init()
    histo=rebin ( hold )
    axes=axisLabels ( topo, tev )
    histo.SetXTitle ( axes["x"] )
    histo.SetYTitle ( axes["y"] )
    if percent:
        histo.Scale(1./100.)
    histo.SetZTitle ( "A #times #varepsilon" )
    histo.SetName("efficiency_%s" % topo )
    histo.SetTitle("efficiency_%s" % topo )
    return histo

def shiftGraph ( graph, xshift=12.5, yshift=12.5 ):
    """ shift the graph by <shift> in x and y """
    if xshift==0. and yshift==0.: return
    x=graph.GetX()
    y=graph.GetY()
    xnew=[]
    ynew=[]
    for i in range( graph.GetN() ):
        graph.SetPoint ( i, x[i]+xshift, y[i]+yshift )
    return graph

def reverseGraph ( g ):
    """ I always want the graph to go from low x values to high x
            values, not the other way round! """
    ## print "[Standardizer.py] reversing graph!"
    x,y=ROOT.Double(0.),ROOT.Double(0.)
    xs,ys=[],[]
    for i in range(g.GetN()):
        g.GetPoint(i,x,y)
        xs.append(float(x))
        ys.append(float(y))

    if len(xs)==0: return g
    n_lts=0
    for i in range(len(xs)-1):
        x=xs[i]
        xp1=xs[i+1]
        if xp1<x:
            n_lts+=1
    f_lts=float(n_lts)/float(len(xs))
    if f_lts>0.5: ## reverse!!!
        print "[Standardizer.py] reverse graph!"
        xs.reverse()
        ys.reverse()
    graph=ROOT.TGraph( len(xs), array('f',xs),array('f',ys))
    return graph

def standardGraph ( g, topo, ymin=0., xmin=100., dropLast=0, dropFirst=0, addBefore=None, addAfter=None, factor=1., dmmin=0., reverse=False, expected=False, plusminussigma=0, cutgraph=False, extendDiagonal=-1. ):
    """ create a standard graph. ignore points below ymin and xmin,
            optionally drop "n" last and/or first points.
            points can also be added via add=[ [x0,y0],[x1,y1],...]
            """
    topo=getCanonicalName ( topo )
    if not g: return None
    if g.GetN()==0: return None
    if reverse:
        g=reverseGraph ( g )
    expstring=""
    pm1=""
    if expected:
        expstring="expected"
    if plusminussigma==1: pm1="p1"
    if plusminussigma==-1: pm1="m1"
    name="%sexclusion%s_%s" % (expstring, pm1, topo )
    if abs(factor-3.)<.01:
        name="%sexclusion3%s_%s" % (expstring, pm1, topo )
    if abs(factor-1./3.)<.01:
        name="%sexclusion13%s_%s" % (expstring, pm1, topo )
    tx,ty=ROOT.Double(0.),ROOT.Double(0.)
    xs,ys=[],[]

    keepFirstYMin=True ## the first point below ymin we keep
    ## (unless it's the first point)
    keepLastDMMin=True
    lastdmmin=None
    if addBefore!=None:
        print "add before=",addBefore
        for point in addBefore:
            xs.append(point[0])
            ys.append(point[1])
    for i in range(dropFirst,g.GetN()-dropLast):
        g.GetPoint(i,tx,ty)
        x=float(tx)
        y=float(ty)
        if y>=ymin and x>=xmin and (x-y)>=dmmin and keepLastDMMin:
            keepLastDMMin=False
            ## print "ok, pull out last dmmin",lastdmmin
            if lastdmmin:
                xs.append(lastdmmin[0])
                ys.append(lastdmmin[1])
        if y>=ymin and x>=xmin and (x-y)>=dmmin:
            xs.append(float(x))
            ys.append(float(y))
        if y<ymin and keepFirstYMin:
            if i>2:
                keepFirstYMin=False
            xs.append(float(x))
            ys.append(float(y))
        if (x-y)<dmmin and keepLastDMMin:
            lastdmmin=[ float(x),float(y) ]
            ## print "set last dmmin",lastdmmin

    if cutgraph:
        validPoints = CutGraph(g,xmin,ymin,dmmin, dropLast=0, dropFirst=0)
        xs=validPoints[0]
        ys=validPoints[1]

    if addAfter!=None:
        print 'add after=', addAfter   #print
        for point in addAfter:
            xs.append(point[0])
            ys.append(point[1])


    if len(xs)==0:
        print "Error: graph was swallowed by constraints"
        return None
    if extendDiagonal>0.:
        print "[Standardizer.py] now we extend the diagonal"
        print "x,y=",xs[0],ys[0],len(xs)
        y=-xs[0]+ys[0]+extendDiagonal
        xs.insert(0,extendDiagonal)
        ys.insert(0,y)
        print "x,y=",xs[0],ys[0],len(xs)
    graph=ROOT.TGraph( len(xs), array('f',xs),array('f',ys))
    graph.SetName(name)
    graph.SetTitle(name)
    graph.SetLineColor ( ROOT.kBlack )
    if expected:
        graph.SetLineColor ( ROOT.kRed )
    graph.SetLineWidth(3)
    if abs(factor-1.)<.01:
        graph.SetLineStyle(1)
    if abs(factor-3.)<.01:
        graph.SetLineStyle(2)
    if abs(factor-1./3.)<.01:
        graph.SetLineStyle(3)
    if plusminussigma!=0:
        graph.SetLineStyle(2)
    return graph

def oldStandardGraph ( graph, topo ):
    topo=getCanonicalName ( topo )
    graph.SetName("exclusion_%s" % topo )
    graph.SetTitle("exclusion_%s" % topo )
    graph.SetLineColor ( ROOT.kBlack )
    return graph

def writeSelectionNames ( s ):
    """ given the selection names as a dictionary,
            with keys from 1 to n, we write the names
            in a pickle file. simple. """
    import pickle
    f=open("selections.pkl","write")
    pickle.dump ( s, f )
    f.close()

def referenceXSecs ( production ):
    import pickle
    f=open("/afs/hephy.at/user/w/walten/public/ReferenceXsecs.pc")
    if not f: print "cant open ref xsecs"
    xsecs=pickle.load(f)[production]
    f.close()
    return xsecs

def minMax ( graph, ymin=0., xmin=None, verbose=False):
    """ actually this is not minimum value and maximum value,
            rather it's lsp=0 gev and delta_m=200 gev limits """
    #print "[Standardizer:minMax] graph=",graph
    if not graph: return [ xmin, 0, 0 ]
    Min=99999.
    dmax=999999.
    Max=0.
    xmax=99999.
    n=graph.GetN()
    x=ROOT.Double(0.)
    y=ROOT.Double(0.)
    #if verbose: print "[Standardizer:minMax] n=",n
    for i in range(n):
        graph.GetPoint(i,x,y)
        d=int(float(x)-float(y))
        d200=abs( float(x)-float(y)-200. )
        if verbose:
            print "[Standardizer:minMax] x=%d y=%d    x-y: %d d200=%f" % ( x,y, d, d200 )
        if float(x)>200. and d<200: continue
        if float(y)<ymin: continue
        # if float(x)<Min: Min=float(x)
        if d200<dmax:
            dmax=d200
            Min=float(x)
        #print "x,y=",x,y
        if float(y)<xmax:
            xmax=float(y)
            Max=float(x)
        if float(y)==xmax and float(x)>Max:
            xmax=float(y)
            Max=float(x)
        #if float(x)>Max: Max=float(x)
        #print "x,y=",x,y,"Min,Max=",Min,Max
    #print "minmax=",xmin,Min,Max
    if Min>99998.: Min=0.
    return [ xmin, Min, Max ]

def minMaxOld ( graph, ymin=0., xmin=None):
    print "[Standardizer:minMax] graph=",graph
    if not graph: return [ xmin, 0, 0 ]
    Min=99999.
    Max=0.
    n=graph.GetN()
    x=ROOT.Double(0.)
    y=ROOT.Double(0.)
    #print "n=",n
    for i in range(n):
        graph.GetPoint(i,x,y)
        d=int(float(x)-float(y))
        #print "point:x=%d y=%d    x-y: %d" % ( x,y, d )
        if x>200 and d<200: continue
        if float(y)<ymin: continue
        if float(x)<Min: Min=float(x)
        if float(x)>Max: Max=float(x)
        #print "x,y=",x,y,"Min,Max=",Min,Max
    #print "minmax=",xmin,Min,Max
    if Min>99998.: Min=0.
    return [ xmin, Min, Max ]

def writeMinMax ( f, minmax, expected=False, plusminussigma=0 ):
    title="exclusions"
    if expected: title="expectedexclusions"
    if plusminussigma == 1: title = title+'p1'
    if plusminussigma == -1: title = title+'m1'
    for (topo,mm) in minmax.items():
        if mm[2]>0 or mm[1]<100000:
            w="%s: %s %d %d\n" % ( title, getCanonicalName(topo),mm[1],mm[2] )
            if mm[0]:
                w="%s: %s %d %d %d\n" % ( title, getCanonicalName(topo),mm[0],mm[1],mm[2] )
            f.write ( w )

def mend ( histogram, positions ):
    """ mend holes in a histogram.
            positions is an array of
            [ xhole, yhole, [ points-to-interpolate ] ]
            points-to-interpolate (pti) is an array of [x,y] values
    """
    nx=histogram.GetXaxis().GetNbins()
    ny=histogram.GetYaxis().GetNbins()
    for x in range(nx+1):
        for y in range(ny+1):
            c=histogram.GetBinContent(x,y)
            mgl=histogram.GetXaxis().GetBinCenter(x)
            mlsp=histogram.GetYaxis().GetBinCenter(y)
            for cpositions in positions:
                if mgl==cpositions[0] and mlsp==cpositions[1]:
                    c=0.
                    for pti in cpositions[2]:
                        c+=histogram.GetBinContent(x+pti[0],y+pti[1])
                    histogram.SetBinContent(x,y,c/float(len(pti)))

def CutGraph(g,xmin,ymin,dmmin, dropLast=0, dropFirst=0):
    """keep only points inside a region defined by
         xmin, ymin, and x-y = dmmin and create a point of intersection
         on the edge of the region"""
    if xmin == None:
        xmin = 0.
    x, y = ROOT.Double(0.), ROOT.Double(0.)
    xnext, ynext = ROOT.Double(0.), ROOT.Double(0.)
    xnew, ynew = [], []

    for i in range(dropFirst,g.GetN()-dropLast):

        g.GetPoint(i,x,y)
        g.GetPoint(i+1,xnext,ynext)
        xp, yp = [float(x) ,float(xnext)], [float(y) ,float(ynext)]
        xs, ys = [], []
        xsort, ysort = [], []
        ZDE = False

        try:                                                                 # produce a line defined by 2 points of the exclusionline
            k = (yp[1]-yp[0])/(xp[1]-xp[0])
            d = yp[0]-xp[0]*k
        except ZeroDivisionError: ZDE = True

        if ZDE == False:                 # if line is not parallel to edges => caculate the points of intersection with the edges
            xs.append(xmin)                                             # first edge
            ys.append(k*xs[0] + d)
            if k != 1.:                                                    # second edge
                xs.append((d+dmmin)/(1.-k))
                ys.append(k*xs[1]+d)
            if k != 0.:                                                 # third edge
                ys.append(ymin)
                xs.append((ymin-d)/k)

        if ZDE == True:
            xs.append(xp[0])                                         # second edge
            ys.append(xp[0]-dmmin)
            xs.append(xp[0])                                        # third edge
            ys.append(ymin)

        for j in range(len(xs)):                # only intersection between the 2 points of the exclusionline
            if (xp[0] <= xs[j] <= xp[1]) or (xp[0] >= xs[j] >= xp[1]):
                if (yp[0] <= ys[j] <= yp[1]) or (yp[0] >= ys[j] >= yp[1]):
                    for l in range(1, len(xp)):
                        if ((xs[j]-xp[0])**2 + (ys[j]-yp[0])**2) < ((xp[l]-xp[0])**2 + (yp[l]-yp[0])**2):        # sorts all the intersections between point and next point
                            xp.insert(l,xs[j])
                            yp.insert(l,ys[j])
                            break
                    #print "Standardizer:CutGraph", xp, yp

        for j in range(len(xp)):                    # feed points inside selected region into returnvalue
            if math.floor(xp[j])+1 >= xmin and math.floor(yp[j])+1 >= ymin and math.floor(xp[j]-yp[j])+1 >= dmmin:        # floor to avoid problems with float
                if xnew != [] and ynew != []:
                    if xp[j] == xnew[-1] and yp[j] == ynew[-1]:
                        continue
    xnew.append(round(xp[j],0))
    ynew.append(round(yp[j],0))

    #print 'return: xnew, ynew: ', xnew, ynew
    if len(xnew) == 0:
        print '[Standardizer.CutGraph]: no points left'
        return [[0.], [0.]]
    return [xnew,ynew]


def identicalFiles ( f1, f2 ):
    """ compare f1 with f2, return True if theyre identical """
    ff1=open(f1,"r")
    ff1l=ff1.readlines()
    ff1.close()
    ff2=open(f2,"r")
    ff2l=ff2.readlines()
    ff2.close()
    return ff1l==ff2l

## the new way to define the meta info is via variables
#info={"lumi":None, "minmax":None, "contact": None, "pas": None, "missing": None,
#            "url": None, "expectedminmax": None,
#            "minmaxp1": None, "minmaxm1": None, "requires": None }
info={}
condition={}
fuzzycondition={}
constraint={}
unconstraint={}
category={}

def writeInfo(lumi=None, minmax=None, contact=None, pas=None, missing=None,
              public=True, nll=False, url=None, expectedminmax=None,
              minmaxp1=None, minmaxm1=None, requires=None):
    """writes the info about the exclusion limits, plus the lumi into info.txt.
    """
    import os
    keys = [
        "lumi", "minmax", "pas", "url", "contact", "expectedminmax",
        "requires", "figures", "minmaxp1", "minmaxm1", "checked", "journal",
        "bibtex", "x", "sqrts", "public", "nll", "prettyname", "order",
        "comment", "dictionary", "axes", "publisheddata", "missing",
        "private_topologies","superseded_by","arxiv","journal", "publication", 
        'limit_unit', 'supersedes','lastUpdate'
    ]
    makeDicts() # before we start, we write out the ul dictionaries
    for (key,value) in info.items():
        if key not in keys:
            print "[Standardizer.py] warning when writing info.txt: Do not know key ``%s''." % key
    if os.path.exists ( "info.txt" ):
        os.system ( "cp info.txt info.txt_" )
    f=open("info.txt","w")
    if info.has_key ( "sqrts" ):
        try:
            l = info['sqrts'].split()
            f.write ( "sqrts: %.2f %s\n" %(float(l[0].strip()),l[1]) )
            print "[Standardizer.py] info when writing sqrts to info.txt: Got unit %s." %l[1]
        except AttributeError:
            f.write ( "sqrts: %.2f\n" % info["sqrts"] )
    if lumi:
        f.write ( "lumi: %.2f\n" % lumi )
    else:
        if info.has_key ("lumi"):
            try:
                l = info['lumi'].split()
                f.write ( "lumi: %.2f %s\n" %(float(l[0].strip()),l[1]) )
                print "[Standardizer.py] info when writing lumi to info.txt: Got unit %s." %l[1]
            except AttributeError:
                f.write ( "lumi: %.2f\n" % info["lumi"] )
    if info.has_key('limit_unit'):
        f.write('limit_unit: %s\n' %info['limit_unit']) 
    if minmax:
        writeMinMax ( f, minmax, False )
    else:
        if info.has_key ( "minmax" ): writeMinMax ( f, info["minmax"], False )
    if expectedminmax:
        writeMinMax ( f, expectedminmax, True )
    else:
        if info.has_key ( "expectedminmax" ):
            writeMinMax ( f, info["expectedminmax"], True )
    if minmaxp1:
        writeMinMax ( f, minmaxp1, plusminussigma=1 )
    else:
        if info.has_key ( "minmaxp1" ):
            writeMinMax ( f, info["minmaxp1"], plusminussigma=1 )
    if minmaxm1:
        writeMinMax ( f, minmaxm1, plusminussigma=-1 )
    else:
        if info.has_key ( "minmaxm1" ):
            writeMinMax ( f, info["minmaxm1"], plusminussigma=-1 )
    if contact:
        f.write ( "contact: %s\n" % contact )
    else:
        if info.has_key ( "contact" ):
            f.write ( "contact: %s\n" % info["contact"] )
    if pas:
        f.write ( "pas: %s\n" % pas )
    else:
        if info.has_key ( "pas" ):
            f.write ( "pas: %s\n" % info["pas"] )
    if missing:
        f.write ( "missing: %s\n" % missing )
    else:
        if info.has_key ( "missing" ):
            f.write ( "missing: %s\n" % info["missing"] )
    if info.has_key ( "prettyname" ):
            f.write ( "prettyname: %s\n" % info["prettyname"] )
    if url:
        f.write ( "url: %s\n" % url )
    else:
        if info.has_key ( "url" ):
            f.write ( "url: %s\n" % info["url"] )
    if info.has_key ( "x" ):
            f.write ( "x: %s\n" % info["x"] )
    if requires:
        f.write ( "requires: %s\n" % requires )
    else:
        if info.has_key ( "requires" ):
            f.write ( "requires: %s\n" % info["requires"] )
    if info.has_key ( "checked" ):
        f.write ( "checked: %s\n" % info["checked"] )
    if info.has_key ( "publisheddata" ):
        f.write ( "publisheddata: %s\n" % info["publisheddata"] )
    f.write ( "private: %d\n" % (not public) )
#    order="nlonll" if nll else "nlo"
    if info.has_key("private_topologies"):
        f.write("private_topologies: %s\n" % info["private_topologies"])
    if info.has_key("order"):
        order=info["order"]
        f.write ( "order: %s\n" % order )
    if info.has_key ( "dictionary" ):
        f.write ( "dictionary: %d\n" % info["dictionary"])
    if info.has_key ( "figures" ):
        f.write ( "figures: %s\n" % info["figures"] )
    if info.has_key ( "journal" ):
        f.write ( "journal: %s\n" % info["journal"] )
    if info.has_key ( "arxiv" ):
        f.write ( "arxiv: %s\n" % info["arxiv"] )
    if info.has_key ( "publication" ):
        f.write ( "publication: %s\n" % info["publication"] )
    if info.has_key ( "bibtex" ):
        f.write ( "bibtex: %s\n" % info["bibtex"] )
    if info.has_key ("comment"):
        f.write ( "comment: %s\n" % info["comment"] )
    if info.has_key ( "superseded_by" ):
        f.write ( "superseded_by: %s\n" %info["superseded_by"] )
    if info.has_key ( "supersedes" ):
        f.write ( "supersedes: %s\n" %info["supersedes"] )
    if len(condition)>0:
        for (key,value) in condition.items():
            f.write ( "condition: %s -> %s\n" % (getCanonicalName(key),value) )
    if len(fuzzycondition)>0:
        for (key,value) in fuzzycondition.items():
            f.write ( "fuzzycondition: %s -> %s\n" % (getCanonicalName(key),value) )
    if len(constraint)>0:
        for (key,value) in constraint.items():
            f.write ( "constraint: %s -> %s\n" % (getCanonicalName(key),value) )
    if len(unconstraint)>0:
        for (key,value) in unconstraint.items():
            f.write ( "unconstraint: %s -> %s\n" % (getCanonicalName(key),value) )
    if len(category)>0:
        for (key,value) in category.items():
            f.write ( "category: %s -> %s\n" % (getCanonicalName(key),value) )
    if info.has_key("axes"):
        f.write ("axes: %s\n" %info["axes"])
    if info.has_key("lastUpdate"):
        CheckDateFormat(info["lastUpdate"])
        f.write ("lastUpdate: %s\n" %info["lastUpdate"])
    f.close()
    if os.path.exists ( "info.txt_" ) and not identicalFiles ( "info.txt_", "info.txt" ):
        ## if we have a temporary backup file info.txt_ and something has changed between the current info.txt and the temporary backup file, then the temporary backup file will be
        ## saved as the lasting backup file info.old
        os.system ( "cp info.txt_ info.old" )
        

def CheckDateFormat(date):
    """Check if Date is in Format: YYYY/MM/dd
    exit raise ValueError
    
    """
    if not isinstance(date,str):
        raise ValueError('Date have to be formated as YYYY/MM/DD, got %s' %date)
    try:
        year, month, day = date.split('/')
        year, month, day = int(year), int(month), int(day)
    except ValueError:
        raise ValueError('Date have to be formated as YYYY/MM/DD, got %s' %date)
    if year < 2013 or year > 2100:
        raise ValueError('Year have to be between 2013 and 2100, got %s' %year)
    if month < 1 or month > 12:
        raise ValueError('Month have to be between 1 and 12, got %s' %month)
    if day < 1 or day > 31:
        raise ValueError('day have to be between 1 and 31, got %s' %day)
    return
        
def getTGraphViaPDF( filename ):
    """ returns a TGraph from a txt file with coorinates in svg format
            first line in txt file needs scaling information"""
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    n = len(lines)
    g = ROOT.TGraph(n-1)
    i = 0
    xorig = 0
    yorig = 0
    if 'm' in lines[0].split()[0]:
        relative = True
    elif 'M' in lines[0].split()[0]:
        relative = False
    else:
        print '[Standardizer.py]: Don\'t know what %s (svg) means!!' %lines[0].split()[0]
    ticks = lines[0].split()
    xticks = []
    yticks = []
    for tick in ticks[1:]:
        if tick.split(':')[0][:1] == 'x':
            xticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
            if tick.split(':')[0][-3:] != 'GeV':
                print '[Standardizer.py]: x-axis in %s!!!' %tick.split(':')[0][-3:]
        elif tick.split(':')[0][:1] == 'y':
            yticks.append([float(tick.split(':')[0][1:-3]),float(tick.split(':')[1])])
            if tick.split(':')[0][-3:] != 'GeV':
                print '[Standardizer.py]: y-axis in %s!!!' %tick.split(':')[0][-3:]
        else:
            print '[Standardizer.py]: Unknown axis %s' %tick.split(':')[0][:1]
    if len(xticks) != 2:
        print '[Standardizer.py]: Too much/less information about the x-axis!'
    if len(yticks) != 2:
        print '[Standardizer.py]: Too much/less information about the y-axis!'    
    xGeV = (xticks[1][1]-xticks[0][1])/(xticks[1][0]-xticks[0][0])
    yGeV = (yticks[1][1]-yticks[0][1])/(yticks[1][0]-yticks[0][0])
    x0 = xticks[0][1] - xticks[0][0]*xGeV
    y0 = yticks[0][1] - yticks[0][0]*yGeV
    if relative:
        for l in lines[1:]:
            v = l.split(' ')
            xorig += float(v[0])
            yorig += float(v[1])
            x = (xorig-x0)/xGeV
            y = (yorig-y0)/yGeV
            g.SetPoint(i,x,y)
            i += 1
        return g
    else:
        for l in lines[1:]:
            v = l.split(' ')
            xorig = float(v[0])
            yorig = float(v[1])
            x = (xorig-x0)/xGeV
            y = (yorig-y0)/yGeV
            g.SetPoint(i,x,y)
            i += 1
        return g

def getTGraphFromTXTFile( filename ):
    """ returns a TGraph from a txt file with x and y coordinates in two columns """ 
    f = open( filename, 'r')
    points = f.readlines()
    points = sorted(points, key = lambda x: float(x.split()[0]))
    f.close()
    n = len(points)
    g = ROOT.TGraph(n)
    i = 0
    for point in points:
        g.SetPoint( i, float(point.split()[0]), float(point.split()[1]) )
        i += 1
    return g
    

massplitting={"TChiWZ": 86., "T6bbWW": 86., "T1tttt": 338.}

def splitHisto( hist,mz =""):
    """ splits an upper limit histogram into an on-shell and an off-shell one"""
    nx = hist.GetNbinsX()
    ny = hist.GetNbinsY()
    h_on = copy.deepcopy(hist)
    h_off = copy.deepcopy(hist)
    name = hist.GetName()
    topo = None
    for topology in massplitting:
        if topology in name: topo = topology
    if not topo:
        logger.error("Please define mass splitting for topology of histo %s in \
        the dictionary\"massplitting\"!" %name)
    h_on.SetName(name + mz)
    h_off.SetName(name + "off" + mz)
    h_on.SetTitle(name + mz)
    h_off.SetTitle(name + "off" + mz)
    for bx in range(1, nx+1):
        for by in range(1, ny+1):
            mx = hist.GetXaxis().GetBinCenter(bx)
            my = hist.GetYaxis().GetBinCenter(by)
            if mx-my < massplitting[topo]:
                h_on.SetBinContent(bx, by, 0.)
            else:
                h_off.SetBinContent(bx, by, 0.)
    return h_on, h_off

def splitDict( topo, mz="", dict=None, expected=False ):
    """ splits an upper limit dictionary into an on-shell and an off-shell one.
        the mass splitting, defining on- and off-shell region, is defined in the dictionary massplitting (for TChiWZ: 91-2*2.5=86,
        T1ttt: 2*(173-2*2))"""
    if not massplitting[getCanonicalName(topo)]:
       logger.error("Please define mass splitting for %s in the dictionary \"massplitting\"!" %topo)
    if not dict:
       if expected:
           try:
               dict = expecteddict[getCanonicalName(topo)+mz]
           except Exception, e:
               print e
       else:
           try:
               dict = dictionaries[getCanonicalName(topo)+mz]
           except Exception, e:
               print e
    topo_on = getCanonicalName(topo)+mz
    topo_off = getCanonicalName(topo)+'off'+mz
    Dict_on={}
    Dict_off={}
    for mx in dict:
        for my in dict[mx]:
            if mx-my > massplitting[topo]:
                if not Dict_on.has_key(mx):
                    Dict_on[mx]={my:dict[mx][my]}
                else:
                    Dict_on[mx][my]= dict[mx][my]
            else:
                if not Dict_off.has_key(mx):
                    Dict_off[mx]={my:dict[mx][my]}
                else:
                    Dict_off[mx][my]= dict[mx][my]
    if expected:
        expecteddict[topo_on]=Dict_on
        expecteddict[topo_off]=Dict_off    
    else:
        dictionaries[topo_on]=Dict_on
        dictionaries[topo_off]=Dict_off    

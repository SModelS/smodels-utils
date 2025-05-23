#!/usr/bin/python

import os,sys
import time
import glob
import commands
home = os.path.expanduser("~")
sys.path.append(os.path.join(home,'smodels'))
from smodels.tools import statistics
    
fastlimdir="../fastlim-1.0/analyses_info/8TeV/"
efficienciesdir="../fastlim-1.0/efficiency_tables/"
databasedir = "../../../smodels-database/"
destdir="%s/8TeV/ATLAS/" % databasedir

dictionary=None
def openDictionary():
    dictionary=open("%s/signalregions.py" % databasedir, "w" )
SRs={}

def removeExp ( exp ):
    cmd = "rm -r %s/%s-eff" % ( destdir, exp )
    print "[convertHelpers] %s" % cmd
    commands.getoutput ( cmd )

def createDataInfoFile ( analysis, cut ):
    """ create the datainfo file for analysis, signalregion ANAana-CUTcut """
    print "[fastlimHelpers] now createDataInfoFile for",analysis,cut
    if not analysis in SRs:
        SRs[analysis]={}
    destdir="%s/8TeV/ATLAS/" % databasedir
    newananame=analysis.replace("_","-")+"-eff"
    datadir="/data-cut%d" % ( cut )
    dataInfoFile=destdir+newananame+datadir+ "/dataInfo.txt"
    if os.path.exists ( dataInfoFile ):
        print "[fastlimHelpers.createDataInfoFile]",dataInfoFile,"exists already."
#        return

    if not os.path.exists ( destdir+newananame ):
        print "creating",destdir+newananame
        os.mkdir ( destdir + newananame )
    ## datadir="/ANA%d-CUT%d" % ( ana, cut )
    if not os.path.exists ( destdir+newananame+datadir ):
        print "creating",destdir+newananame+datadir
        os.mkdir ( destdir+newananame+datadir )
    # fastlimdir="/home/walten/Downloads/fastlim-1.0/analyses_info/8TeV/"
    infofile=open ( fastlimdir + analysis + "/SR_info.txt" )
    lines=infofile.readlines()
    infofile.close()
    tokens=lines[cut+1].split()
    lumi,data,bg,sys,sr=float(tokens[1]),float(tokens[2]),float(tokens[3]),float(tokens[4])," ".join(tokens[10:])
    ul=float(tokens[7])
    eul=statistics.upperLimit ( bg, bg, sys, lumi, .05 )

    f=open ( destdir+newananame+datadir+ "/dataInfo.txt", "w")
    f.write ( "dataType: efficiencyMap\n" )
    my_sr = sr.replace("/","")
    # f.write ( "dataId: data-cut%d\n" % ( cut ) )
    f.write ( "dataId: %s\n" % ( my_sr ) )
    f.write ( "observedN: %d\n" % data )
    f.write ( "expectedBG: %.1f\n" % bg )
    f.write ( "bgError: %.1f\n" % sys )
    s_ul = float('%.3g' % ul ) ## round to n significant numbers
    f.write ( "upperLimit: %g*fb\n" % s_ul )
    s_eul = float ('%.3g' % eul )
    f.write ( "expectedUpperLimit: %g*fb\n" % s_eul )
    ## float('%.2g' % 0.0123435456)
    ## f.write ( "signalRegion: %s\n" % sr )
    print("[SRs[analysis][datadir]=sr")
    SRs[analysis][datadir]= my_sr
    f.close ()
    print "[fastlimHelpers] done creating",destdir+newananame+datadir+ "/dataInfo.txt"

def createInfoFile ( analysis ):
    """ creates info.txt """

    newananame=analysis.replace("_","-")+"-eff"
    newexpid=analysis.replace("_","-")
    if not os.path.exists ( destdir+newananame ):
        print "creating",destdir+newananame
        os.mkdir ( destdir + newananame )
    infofile=open ( fastlimdir + analysis + "/SR_info.txt" )
    lines=infofile.readlines()
    infofile.close()
    tokens=lines[1].split()
    sqrts,lumi,data,bg,sys=int(tokens[0]),float(tokens[1]),float(tokens[2]),float(tokens[3]),float(tokens[4])
    f=open ( destdir + newananame + "/globalInfo.txt", "w" )
    f.write ( "sqrts: %d*TeV\n" % sqrts )
    f.write ( "lumi: %.1f/fb\n" % lumi )
    f.write ( "id: %s\n" % newexpid )
    f.write ( "url: https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/%s/\n" % newexpid )
    f.write ( "implementedBy: WW\n" )
    f.write ( "contact: fastlim\n" )
    f.write ( "comment: created from fastlim-1.0\n" )
    f.write ( "lastUpdate: %s\n" % time.strftime("%Y/%m/%d") )
    f.close()

def existsAnalysisCut ( analysis, ana, cut ):
    """ does <analysis>-ANA<ana>-CUT<cut> exist? """
    dirs=glob.iglob ( efficienciesdir+ "/*/" )
    for dir in dirs:
        dir8tev= dir + "/8TeV/" 
        if not os.path.exists ( dir8tev + "/" + analysis ):
            continue
        for j in os.listdir ( dir8tev + "/" + analysis ):
#            print "j=",j
            if j == "ana_%d_cut_%d.effi" % ( ana, cut ):
                return True
    return False

def copyEffiFiles ( analysis, ana, cut ):
    """ copy the .effi files to their proper place in the database """
    Dict = smodels2fastlim('Dict')

    for (key,value) in Dict.items():
        Dict[value]=key
    newananame=analysis.replace("_","-")+"-eff"
    Tnames=[]

    for Fastlimname in os.listdir ( efficienciesdir ):
        if not Fastlimname in Dict.keys():
          continue
        Tname=Dict[Fastlimname]
        print("[convertHelpers.py] %s <- %s" % ( Tname,Fastlimname ) )
        anadir = efficienciesdir+"/"+Fastlimname + "/8TeV/" + analysis
        if not os.path.exists ( anadir ):
#            print "[fastlimHelpers] ",anadir,"does not exist."
            continue
        effifile = anadir + "/ana_%d_cut_%d.effi" % ( ana, cut ) 
        if not os.path.exists ( effifile ):
            print "[fastlimHelpers] ",effifile,"does not exist."
            continue
        realdestdir="%s/%s/data-cut%d/orig/" % ( destdir, newananame, cut  )
        if not os.path.exists ( realdestdir ):
            cmd="mkdir -p %s" % realdestdir
            commands.getoutput ( cmd )
        if os.path.exists ( "%s/%s.effi" % ( realdestdir, Tname ) ):
            print "[convertHelpers] %s/%s.effi exists already" % ( realdestdir, Tname )
            continue
        cmd="cp %s %s/%s.effi" % ( effifile, realdestdir, Tname )
        Tnames.append ( Tname )
        print "[fastlimHelpers.copyEffiFiles] cmd=",cmd
        o=commands.getoutput ( cmd )
        if o!="": print "[copyEffiFiles]",o  
    exclusiondir = efficienciesdir+"../exclusion_lines/" + analysis.replace("_","-")
    if not os.path.exists ( exclusiondir ):
        print "[copyEffiFiles] no exclusion line found"
# print os.listdir ( exclusiondir)
    for file in glob.iglob ( exclusiondir+ "/*_excl.dat" ):
        tname = os.path.basename(file[:-9])
        print "[copyEffiFiles] found",file,"is there",tname,"in",Tnames,"?"
        if tname in Tnames:
          cmd="cp %s %s/" % ( file, realdestdir )
          print "[copyEffiFiles] cmd",cmd
          commands.getoutput ( cmd )

def createAndRunConvertFiles ( analysis, cut, dry_run=False ):
    """ create the proper convert.py file """
    print "[fastlimHelpers] createAndRunConvertFiles"
    newananame=analysis.replace("_","-")+"-eff"
    realdestdir="%s/%s/data-cut%d/" % ( destdir, newananame, cut  )
    cmd="cp ./convert.py %s" % realdestdir
    print "[createAndRunConvertFiles] >>%s<<" % cmd
    commands.getoutput ( cmd )
    cmd= "cd %s; ./convert.py" % realdestdir
    print "[createAndRunConvertFiles] >>%s<<" % cmd
    o=None
    if not dry_run:
        o=commands.getoutput ( cmd )
        print "[createAndRunConvertFiles] out",o


def mergeSmsRootFiles ( analysis ):
    ## wait! if there exists an UL analysis of the same name, why dont we copy sms.root from there?
    ULananame=analysis.replace("_","-")
    newananame=analysis.replace("_","-")+"-eff"
    ULsmsroot = destdir + "/" + ULananame + "/sms.root" 
    if os.path.exists ( ULsmsroot ):
        import commands
        cmd = "cp %s %s/%s/" % ( ULsmsroot, destdir,newananame )
        print "[fastlimHelpers.mergeSmsRootFiles] cmd=",cmd
        commands.getoutput ( cmd )
        return
    import ROOT
    targetsmsname=destdir + "/" + newananame + "/sms.root"
    write=ROOT.TFile ( targetsmsname, "recreate" )
    print "[fastlimHelprswriting to",targetsmsname
    has=[]
    for i in os.listdir ( destdir + "/" + newananame ):
        if i[:4]!="data": continue
        smsfilename=destdir + "/" + newananame + "/" + i+"/sms.root" 
        print "reading from",smsfilename
        read=ROOT.TFile ( smsfilename )
        keys=read.GetListOfKeys()
        n=keys.GetSize()
        for i in range(n):
            dir=keys.At(0).GetTitle()
            if dir in has:
                continue
            write.mkdir ( dir )
            write.cd ( dir )
            tdir=read.Get(dir )
            obj= tdir.GetListOfKeys().At(0)
            obj2=obj.ReadObj().Clone()
            write.cd ( dir )
            obj2.Write()
            has.append ( dir )
    write.Write()
    write.Close()
    for i in os.listdir ( destdir + "/" + newananame ):
        if i[:4]!="data": continue
        smsfilename=destdir + "/" + newananame + "/" + i+"/sms.root" 
        # print "deleting",smsfilename
        if os.path.exists ( smsfilename ):
             os.unlink ( smsfilename )

def copyValidationScripts ( expid ):
    """ this little method should just copy validate.py, validateTx.py and
        plotValidation.py to the destination """
    return
    """
    print "[fastlimHelpers.copyValidationScripts] expid=",expid
    destination=destdir+expid.replace("_","-")+"-eff"
    cmd="mkdir %s/validation" % destination
    print "[fastlimHelpers.copyValidationScripts]",cmd
    import commands
    commands.getoutput ( cmd )
    cmd="cp /home/walten/git/smodels-utils/validation/scripts/*.py %s/validation/" % destination
    print "[fastlimHelpers.copyValidationScripts]",cmd
    commands.getoutput ( cmd )
    """
    
def smodels2fastlim(txname):
    """
    Converts the SModelS Txname (i.e. T2tt) to a fastlim notation (i.e. T1tN1_T1tN1)
    :param txname: Txname in string notation (i.e. T2tt). If txname=Dict returns
                    the full dictionary
    :return: Txname in fastlim notation (string) or the dictionary (if txname = Dict). 
    """
    
    Dict = { "GbB1tN1_GbB1tN1": "T5btbt", "GtT1bN1_GtT1tN1": "T5tbtt", 
             "GgN1_GqqN1": "TGQ",
             "GtT1bN1_GtT1bN1": "T5tbtb", "GgN1_GgN1": "T2", "GbtN1_GgN1": "TGQbtq",
             "GbbN1_GgN1": "TGQbbq", "GttN1_GttN1": "T1tttt", "GbbN1_GbbN1": "T1bbbb",
             "GbB1bN1_GbB1bN1": "T5bbbb", "GbbN1_GqqN1": "T1bbqq",
             "T1tN1_T1tN1": "T2tt", "GgN1_GttN1": "TGQqtt", 'GbbN1_GbtN1': "T1bbbt",
             'GqqN1_GttN1': "T1qqtt", 'T1bN1_T1bN1': "T2bb", 'GbtN1_GbtN1': "T1btbt",
             'GbtN1_GqqN1': "T1btqq", 'GbtN1_GttN1': "T1bttt", 'T1bN1_T1tN1': "T2bt",
             'GbbN1_GttN1': "T1bbtt", 'GqqN1_GqqN1': "T1",
             "GbB1bN1_GbB1tN1": "T5bbbt", "GtT1tN1_GtT1tN1": "T5tttt",
#Added (Andre - 11/11/2015):             
             "B1bN1_B1bN1" : "T2bb", "T2tN1_T2tN1" : "T2tt", "T1tN1_T1tN1" : "T2tt",
             "B2bN1_B2bN1" : "T2bb", "GbB2bN1_GbB2bN1" : "T5bbbb", 
             "GtT2tN1_GtT2tN1" : "T5tttt", "GbB2tN1_GbB2tN1": "T5btbt", 
             "GbB2bN1_GbB2tN1" : "T5bbbt", "GtT2bN1_GtT2bN1" : "T5tbtb",
             "T2bN1_T2bN1" : "T2bb", "T2bN1_T2tN1" : "T2bt",
#Added (Andre - 02/13/2016):
             "B1tN1_B1tN1" : "T2tt","B2tN1_B2tN1" : "T2tt", "B1bN1_B1tN1" : "T2bt", 
             "B2bN1_B2tN1" : "T2bt" 
    }
    
    if txname == 'Dict': return Dict
    
    for f,tx in Dict.items():
        if tx == txname: return f
        
    return None


def closeDictionaryFile():
    print "currently we dont write a dict file"
    return
    dictionary.write ( "SRs={" )
    for analysis,cuts in SRs.items():
        dictionary.write ( '"%s":{' % analysis )
        for cut,region in cuts.items():
            dictionary.write ( '"%s":"%s", ' % ( cut.replace("/",""), region ) ) 
        dictionary.write ( "}," )
    dictionary.write ( "}\n" )
    dictionary.close()


def fastlimPIDsFor(txname):
    """
    Converts the SModelS Txname (i.e. T2tt)
    to the corresponding list of PIDs appearing in the specific decay assumed by Fastlim.
    :param txname: Input txname (i.e. T2tt)
    :return: List of PIDs appearing in txname according to Fastlim. 
    """
    
    fastlimNames = []
    for fast,smod in smodels2fastlim('Dict').items():
        if smod == txname: 
            fastlimNames.append(fast)
    if not fastlimNames: return []
    
    pidsDict = {}
    
    pidsDict["GbB1tN1_GbB1tN1"] = [[[1000021,1000005,1000022],[1000021,1000005,1000022]],
                                    [[1000021,2000005,1000022],[1000021,2000005,1000022]]] 
    pidsDict["GtT1bN1_GtT1tN1"] = [[[1000021,1000006,1000022],[1000021,1000006,1000022]],
                                    [[1000021,2000006,1000022],[1000021,2000006,1000022]]]
    pidsDict["GgN1_GqqN1"] =  [[[1000021,1000022],[1000021,1000022]]]
    pidsDict["T1tN1_T1tN1"] =  [ [[1000006,1000022], [1000006,1000022]], 
                                [[2000006,1000022], [2000006,1000022]] ]
    pidsDict["B1bN1_B1bN1"]  =  [ [[1000005,1000022], [1000005,1000022]], 
                                [[2000005,1000022], [2000005,1000022]] ]     
    pidsDict["GgN1_GttN1"] =  pidsDict["GgN1_GqqN1"] 
    pidsDict['GbbN1_GbtN1'] =  pidsDict["GgN1_GqqN1"]
    pidsDict['GqqN1_GttN1'] =  pidsDict["GgN1_GqqN1"] 
    pidsDict['T1bN1_T1bN1'] =  pidsDict["T1tN1_T1tN1"] 
    pidsDict['GbtN1_GbtN1'] =  pidsDict["GgN1_GqqN1"]
    pidsDict['GbtN1_GqqN1'] =  pidsDict["GgN1_GqqN1"] 
    pidsDict['GbtN1_GttN1'] =  pidsDict["GgN1_GqqN1"] 
    pidsDict['T1bN1_T1tN1'] =  pidsDict["T1tN1_T1tN1"]
    pidsDict['GbbN1_GttN1'] =  pidsDict["GgN1_GqqN1"] 
    pidsDict['GqqN1_GqqN1'] =  pidsDict["GgN1_GqqN1"]
    pidsDict["GbB1bN1_GbB1tN1"] =  pidsDict["GbB1tN1_GbB1tN1"] 
    pidsDict["GtT1tN1_GtT1tN1"] =  pidsDict["GtT1bN1_GtT1tN1"]   
    pidsDict["GtT1bN1_GtT1bN1"] =  pidsDict["GtT1bN1_GtT1tN1"] 
    pidsDict["GgN1_GgN1"] =  pidsDict["GgN1_GqqN1"] 
    pidsDict["GbtN1_GgN1"] =  pidsDict["GgN1_GqqN1"]
    pidsDict["GbbN1_GgN1"] =  pidsDict["GgN1_GqqN1"] 
    pidsDict["GttN1_GttN1"] =  pidsDict["GgN1_GqqN1"] 
    pidsDict["GbbN1_GbbN1"] =  pidsDict["GgN1_GqqN1"]
    pidsDict["GbB1bN1_GbB1bN1"] =  pidsDict["GbB1tN1_GbB1tN1"] 
    pidsDict["GbbN1_GqqN1"] =  pidsDict["GgN1_GqqN1"]     
    pidsDict["T2tN1_T2tN1"]  = pidsDict['T1bN1_T1tN1'] 
    pidsDict["T1tN1_T1tN1"]  = pidsDict['T1bN1_T1tN1']
    pidsDict["B2bN1_B2bN1"]  =  pidsDict["B1bN1_B1bN1"]
    pidsDict["GbB2bN1_GbB2bN1"]  = pidsDict["GbB1tN1_GbB1tN1"] 
    pidsDict["GtT2tN1_GtT2tN1"]  = pidsDict["GtT1bN1_GtT1tN1"]
    pidsDict["GbB2tN1_GbB2tN1"] = pidsDict["GbB2bN1_GbB2bN1"] 
    pidsDict["GbB2bN1_GbB2tN1"]  = pidsDict["GbB2bN1_GbB2bN1"] 
    pidsDict["GtT2bN1_GtT2bN1"]  =  pidsDict["GtT1bN1_GtT1tN1"]
    pidsDict["T2bN1_T2bN1"]  = pidsDict['T1bN1_T1tN1'] 
    pidsDict["T2bN1_T2tN1"]  = pidsDict['T1bN1_T1tN1']
    pidsDict["B1tN1_B1tN1"]  = pidsDict["B1bN1_B1bN1"]
    pidsDict["B2tN1_B2tN1"]  = pidsDict["B1bN1_B1bN1"] 
    pidsDict["B1bN1_B1tN1"]  = pidsDict["B1bN1_B1bN1"] 
    pidsDict["B2bN1_B2tN1"]  = pidsDict["B1bN1_B1bN1"]

    allpids = []
    for fastlimName in fastlimNames:
        pids = [sorted(pid) for pid in pidsDict[fastlimName]]
        allpids += pids
    
    return allpids

#all_exps= [ "ATLAS_CONF_2013_024", "ATLAS_CONF_2013_035",  "ATLAS_CONF_2013_037",
#    "ATLAS_CONF_2013_047", "ATLAS_CONF_2013_048",  "ATLAS_CONF_2013_049", 
#    "ATLAS_CONF_2013_053",  "ATLAS_CONF_2013_054",  "ATLAS_CONF_2013_061",
#    "ATLAS_CONF_2013_062", "ATLAS_CONF_2013_093" 
#]

# all_exps = [ x[:-1] for x in open("expids").readlines() ]

def runExps ( exps ):
    """ run conversions for the given experimental ids """
    for expid in exps:
        createInfoFile ( expid )
        for cut in range(25):
            has_globals=False
            for ana in range(25):
                if existsAnalysisCut ( expid, ana, cut ):
                    copyEffiFiles ( expid, ana, cut )
                    createAndRunConvertFiles ( expid, cut, dry_run=False )
                    if not has_globals:
                        createDataInfoFile ( expid, cut )
                        copyValidationScripts ( expid )
                        has_globals=True
        mergeSmsRootFiles ( expid )

if __name__ == "__main__":
#    createInfoFile ( "ATLAS_CONF_2013_035" )
#    createDataInfoFile ( "ATLAS_CONF_2013_035", 0, 3 )
#    copyEffiFiles ( "ATLAS_CONF_2013_024", 4, 0 )
#    print existsAnalysisCut ( "ATLAS_CONF_2013_024", 1, 1 )
    mergeSmsRootFiles ( "ATLAS_CONF_2013_024" )

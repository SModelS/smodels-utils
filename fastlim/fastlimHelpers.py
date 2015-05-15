#!/usr/bin/python

import os
import time
import glob
import commands
from smodels.tools import statistics
    
fastlimdir="/home/walten/Downloads/fastlim-1.0/analyses_info/8TeV/"
efficienciesdir="/home/walten/Downloads/fastlim-1.0/efficiency_tables/"
destdir="/home/walten/git/smodels-database/8TeV/ATLAS/"

def createDataInfoFile ( analysis, ana, cut ):
    """ create the datainfo file for analysis, signalregion ANAana-CUTcut """
    destdir="/home/walten/git/smodels-database/8TeV/ATLAS/"
    newananame=analysis.replace("_","-")+"-eff"
    if not os.path.exists ( destdir+newananame ):
        print "creating",destdir+newananame
        os.mkdir ( destdir + newananame )
    datadir="/data-ana%d-cut%d" % ( ana, cut )
    if not os.path.exists ( destdir+newananame+datadir ):
        print "creating",destdir+newananame+datadir
        os.mkdir ( destdir+newananame+datadir )
    fastlimdir="/home/walten/Downloads/fastlim-1.0/analyses_info/8TeV/"
    infofile=open ( fastlimdir + analysis + "/SR_info.txt" )
    lines=infofile.readlines()
    infofile.close()
    tokens=lines[cut+1].split()
    lumi,data,bg,sys=float(tokens[1]),float(tokens[2]),float(tokens[3]),float(tokens[4])
    ul=statistics.upperLimit ( data, bg, sys, lumi )

    f=open ( destdir+newananame+datadir+ "/dataInfo.txt", "w")
    f.write ( "datatype: efficiency-map\n" )
    f.write ( "dataid: ANA%d-CUT%d\n" % ( ana, cut ) )
    f.write ( "observedN: %d\n" % data )
    f.write ( "expectedBG: %.1f\n" % bg )
    f.write ( "bgError: %.1f\n" % sys )
    f.write ( "upperLimit: %.2f*fb\n" % ul )
    f.close ()

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
    f=open ( destdir + newananame + "/info.txt", "w" )
    f.write ( "sqrts: %d*TeV\n" % sqrts )
    f.write ( "lumi: %.1f/fb\n" % lumi )
    f.write ( "id: %s\n" % newexpid )
    f.write ( "url: https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/%s/\n" % newexpid )
    f.write ( "implemented_by: WW\n" )
    f.write ( "contact: fastlim\n" )
    f.write ( "comment: created from fastlim-1.0\n" )
    f.write ( "last_update: %s\n" % time.strftime("%Y/%m/%d") )
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
        anadir = efficienciesdir+"/"+Fastlimname + "/8TeV/" + analysis
        if not os.path.exists ( anadir ):
            print "[fastlimHelpers] ",anadir,"does not exist."
            continue
        effifile = anadir + "/ana_%d_cut_%d.effi" % ( ana, cut ) 
        if not os.path.exists ( effifile ):
            continue
#            print "[fastlimHelpers] ",effifile,"does not exist."
        realdestdir="%s/%s/data-ana%d-cut%d/orig/" % ( destdir, newananame, ana, cut  )
        if not os.path.exists ( realdestdir ):
            cmd="mkdir -p %s" % realdestdir
            commands.getoutput ( cmd )
        cmd="cp %s %s/%s.effi" % ( effifile, realdestdir, Tname )
        Tnames.append ( Tname )
#print "cmd=",cmd
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

def createAndRunConvertFiles ( analysis, ana, cut ):
    """ create the proper convert.py file """
    newananame=analysis.replace("_","-")+"-eff"
    realdestdir="%s/%s/data-ana%d-cut%d/" % ( destdir, newananame, ana, cut  )
    cmd="cp ./convert.py %s" % realdestdir
    print "[createAndRunConvertFiles] >>%s<<" % cmd
    commands.getoutput ( cmd )
    cmd= "cd %s; ./convert.py" % realdestdir
    print "[createAndRunConvertFiles] >>%s<<" % cmd
    o=commands.getoutput ( cmd )
    print "[createAndRunConvertFiles] out",o


def mergeSmsRootFiles ( analysis ):
    import ROOT
    newananame=analysis.replace("_","-")+"-eff"
    targetsmsname=destdir + "/" + newananame + "/sms.root"
    write=ROOT.TFile ( targetsmsname, "recreate" )
    print "writing to",targetsmsname
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


def smodels2fastlim(txname):
    """
    Converts the SModelS Txname (i.e. T2tt) to a fastlim notation (i.e. T1tN1_T1tN1)
    :param txname: Txname in string notation (i.e. T2tt). If txname=Dict returns
                    the full dictionary
    :return: Txname in fastlim notation (string) or the dictionary (if txname = Dict). 
    """
    
    Dict = { "GbB1tN1_GbB1tN1": "T5btbt", "GtT1bN1_GtT1tN1": "T5tbtt", "GgN1_GqqN1": "TGQ",
             "GtT1bN1_GtT1bN1": "T5tbtb", "GgN1_GgN1": "T2", "GbtN1_GgN1": "TGQbtq",
             "GbbN1_GgN1": "TGQbbq", "GttN1_GttN1": "T1tttt", "GbbN1_GbbN1": "T1bbbb",
             "GbB1bN1_GbB1bN1": "T5bbbb", "GbbN1_GqqN1": "T1bbqq",
             "T1tN1_T1tN1": "T2tt", "GgN1_GttN1": "TGQqtt", 'GbbN1_GbtN1': "T1bbbt",
             'GqqN1_GttN1': "T1qqtt", 'T1bN1_T1bN1': "T2bb", 'GbtN1_GbtN1': "T1btbt",
             'GbtN1_GqqN1': "T1btqq", 'GbtN1_GttN1': "T1bttt", 'T1bN1_T1tN1': "T2bt",
             'GbbN1_GttN1': "T1bbtt", 'GqqN1_GqqN1': "T1",
             "GbB1bN1_GbB1tN1": "T5bbbt", "GtT1tN1_GtT1tN1": "T5tttt"
    }
    
    if txname == 'Dict': return Dict
    
    for f,tx in Dict.items():
        if tx == txname: return f
        
    return None


if __name__ == "__main__":
#    createInfoFile ( "ATLAS_CONF_2013_035" )
#    createDataInfoFile ( "ATLAS_CONF_2013_035", 0, 3 )
#    copyEffiFiles ( "ATLAS_CONF_2013_024", 4, 0 )
#    print existsAnalysisCut ( "ATLAS_CONF_2013_024", 1, 1 )
    mergeSmsRootFiles ( "ATLAS_CONF_2013_024" )

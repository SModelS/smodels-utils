#!/usr/bin/env python3

import glob, time, subprocess, os, colorama

def pprint ( text ):
    if not os.path.exists ( "logs/" ):
        subprocess.getoutput ( "mkdir logs" )
    print ( text )
    f=open("logs/prod_%s.txt" % time.asctime().replace(" ","_"), "a" )
    f.write ( text +"\n" )
    f.close()

def ma5():
    ma5Files = glob.glob ( "ma5/ANA_T**/Output/CLs_output_summary.dat" )
    ma5Stats={}
    for f in ma5Files:
        p1,p2 = f.find("ANA_"),f.find("jet")
        process = f[p1+4:p2]
        if not process in ma5Stats:
            ma5Stats[process]=0
        ma5Stats[process]+=1
    pprint ( "ma5 production:" )
    keys = list ( ma5Stats.keys() )
    keys.sort()
    for k in keys:
        v=ma5Stats[k]
        pprint ( " - %s: %s summary.dat files" % ( k, v ) )
    goodkeys = {}
    for k in keys:
        p=k.find("_")
        goodkeys[ k[:p] ]=ma5Stats[k]
    return goodkeys

def mg5():
    mg5Files = glob.glob ( "T*jet.*/Events/run_01/tag_1_pythia8_events.hepmc.gz" )
    mg5Stats={}
    for f in mg5Files:
        p1,p2 = f.find("_"),f.find("jet")
        process = f[:p2]
        #topo,njets = f[:p1],f[p1+1:p2]
        if not process in mg5Stats:
            mg5Stats[process]=0
        mg5Stats[process]+=1
    pprint ( "mg5 production:" )
    keys = list ( mg5Stats.keys() )
    keys.sort()
    for k in keys:
        v=mg5Stats[k]
        pprint ( " - %s: %s hepmc files" % ( k, v ) )
    goodkeys = []
    for k in keys:
        p=k.find("_")
        goodkeys.append ( k[:p] )
    return goodkeys

def inDatabase( topos_c ):
    """ whats in the database, but print only topos_c topologies """
    print ("In database" )
    # print ( topos_c )
    dbFiles=glob.glob ("../../smodels-database/13TeV/ATLAS/ATLAS-SUSY-2016-07-eff/orig/T*embaked" )
    stats={}
    for i in dbFiles:
        f=open(i)
        g=eval(f.read())
        f.close()
        topo = os.path.basename ( i ).replace(".embaked","")
        stats[topo]=len(g.keys())
    ks = list ( stats.keys() )
    ks.sort()
    for k in ks:
        if not k in topos_c.keys():
            continue
        beg,end="",""
        if stats[k] < topos_c[k]:
            beg,end=colorama.Fore.GREEN,colorama.Fore.RESET
        pprint ( "%s - %s: %d points --> now %d %s" % ( beg, k, stats[k], topos_c[k], end ) )


def main():
    mg5()
    topos = ma5()
    inDatabase( topos )

if __name__ == "__main__":
    main()

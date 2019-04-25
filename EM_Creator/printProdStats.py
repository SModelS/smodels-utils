#!/usr/bin/env python3

import glob, time, subprocess, os

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

def main():
    mg5()
    ma5()

if __name__ == "__main__":
    main()

#!/usr/bin/env python

""" collect the training points """

import glob, time, shutil, os, subprocess, sys

def clean ( line : str ) -> str:
    return line.replace("+","")

def collect ( folder : str ) -> int:
    files = glob.glob ( f"./{folder}/T*.csv" )
    case = folder[5:] if folder.startswith ( "full_" ) else folder
    outfile = f"{case}.csv"
    first = True
    ct_l = 0
    skipping = 0
    with open ( outfile, "wt" ) as out:
        for fname in files:
            with open ( fname, "rt" ) as f:
                lines = f.readlines()
                if first:
                    out.write ( clean ( lines[0] ) )
                    first = False
                for line in lines[1:]:
                    if "None" in line:
                        continue
                    tokens = line.split(",")
                    tokens = list ( map ( float, tokens ) )
                    min_x, max_x = min(tokens[-8:]), max(tokens[-8:])
                    if max_x > 100*min_x:
                        # print ( "skipping:", max(tokens[-8:]), tokens )
                        skipping+=1
                        continue
                    out.write ( clean ( line ) )
                    ct_l += 1
        out.close()
        print ( f"{outfile}: {ct_l} lines" )
    print ( f"  -- skipped {skipping} lines" )
    return ct_l

def log( n_lines : dict ):
    logfile = "collection.log"
    if os.path.exists ( logfile ):
        backup = "collection.backup"
        shutil.copy ( logfile, backup )
    with open ( logfile, "wt" ) as f:
        f.write ( "{\n" )
        f.write ( f"    'time': {time.asctime()},\n" )
        for k, v in n_lines.items():
            f.write ( f"    '{k}': {v},\n" )
        f.write ( "}\n" )

def collectAll():
    folders = sorted ( d for d in glob.glob ( "./full_*" ) if os.path.isdir ( d ) )
    n_lines = {}
    for folder in folders:
        case = os.path.basename ( folder )
        nl = collect ( case )
        n_lines[case[5:] if case.startswith ( "full_" ) else case] = nl
    log ( n_lines )
    
def postprocess():
    cmd = "cp EWKinos.csv Sleptons.csv ~/git/likelihoods/data/"
    o = subprocess.getoutput ( cmd )
    print ( f"{cmd}: {o}" )
    cmd = "cd ~/git/likelihoods/data && python ./conv_csv_npy.py"
    o = subprocess.getoutput ( cmd )
    print ( f"{cmd}: {o}" )

# tables/1911.12606-1-0/table-Sleptons_bkgonly-Sleptons_patchset-0.csv
# tables/1911.12606-10-0/results-EWKinos_bkgonly-EWKinos_patchset-0.csv

if __name__ == "__main__":
    collectAll()
    # postprocess()

#!/usr/bin/env python3

"""
.. module:: progress.py
   :synopsis: a progress report of all validation jobs

"""

import glob, time, sys
from tqdm import tqdm

class Progress:
    def __init__ ( self ):
        self.show()

    def parse( self ):
        dirs = glob.glob ( "_V*" )
        dirs += glob.glob ( "tmp*" )
        ctr = 0
        while len(dirs)==0:
            print ( f"[progress] could not find any usual directories. will wait a bit." )
            ctr+=1
            time.sleep ( (2.+ctr)**2 )
            if ctr>10:
                print ( f"[progress] waited enough, lets terminate." )
                sys.exit()
        ret = {}
        for d in dirs:
            npoints = len ( glob.glob ( f"{d}/T*slha" ) )
            ndone = len ( glob.glob ( f"{d}/results/T*.py" ) )
            ret[d]= { "npoints": npoints, "ndone": ndone }
        # print ( ret )
        self.stats = ret

    def pprint ( self ):
        print ( "stats", self.stats )

    def show( self ):
        self.parse()
        # self.pprint()
        self.tqdms = {}
        for i,(k,v) in enumerate ( self.stats.items() ):
            n = tqdm ( desc=k, total = v["npoints"], position = i,
                       unit = "pt", bar_format="{desc}: {percentage:3.0f}%|{bar:46}| {n_fmt}/{total_fmt} [{remaining}] {postfix}", colour = "green" )
            self.tqdms[k]=n
        while True:
            time.sleep(.3)
            self.parse()
            for i,(k,v) in enumerate ( self.stats.items() ):
                self.tqdms[k].update ( v["ndone"] - self.tqdms[k].n )


if __name__ == "__main__":
    p = Progress()

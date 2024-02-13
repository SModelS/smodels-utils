#!/usr/bin/env python3

"""
.. module:: progress.py
   :synopsis: a progress report of all validation jobs

"""

import glob, time, sys
from tqdm import tqdm
from typing import Dict

class Progress:
    def __init__ ( self ):
        self.show()

    def parse( self ):
        dirs = glob.glob ( "_V*" )
        dirs += glob.glob ( "tmp*" )
        ndirs = []
        for d in dirs:
            if d.endswith ( ".ini" ) or d.endswith ( ".py" ) or d.endswith(".png"):
                continue
            ndirs.append ( d )
        dirs = ndirs
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

    def updateTQDM ( self, name : str, values : Dict, position : int ):
        """ update an entry in self.tqdms """
        fullname = f"{name:10s}"
        n = tqdm ( desc=fullname, total = values["npoints"], position = position,
                   unit = "pt", bar_format="{desc}: {percentage:3.0f}%|{bar:46}| {n_fmt}/{total_fmt} [{remaining}] {postfix}", colour = "green" )
        self.tqdms[name]=n

    def show( self ):
        self.parse()
        # self.pprint()
        self.tqdms = {}
        for i,(k,v) in enumerate ( self.stats.items() ):
            self.updateTQDM ( k, v, i )
        while True:
            time.sleep(.3)
            self.parse()
            for i,(k,v) in enumerate ( self.stats.items() ):
                if not k in self.tqdms:
                    if k in self.stats:
                        self.updateTQDM ( k, v, i )
                self.tqdms[k].update ( v["ndone"] - self.tqdms[k].n )


if __name__ == "__main__":
    p = Progress()

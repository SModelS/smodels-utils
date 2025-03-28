#!/usr/bin/env python3

"""
.. module:: progress.py
   :synopsis: a progress report of all validation jobs

"""

import glob, time, sys, copy, os
from tqdm import tqdm
from typing import Dict, Union

class Progress:
    def __init__ ( self, dirs : Union[None,str,list] = None, 
                   waitForDirs : bool = True ):
        """ initialise, and start.
        :param dirs: if None, look for _V* and tmp* directories, else
        consider only the directories given.
        :param waitForDirs: if true, then wait for directories to appear.
        if false, stop, if no directories found
        """
        self.waitForDirs = waitForDirs
        self.previous = {}
        self.stats = {}
        self.dirs = dirs
        self.parse( )
        self.show()

    def getDirs ( self, dirs : Union[None,str,list] = None ) -> list:
        """ given the user's specification of the directories,
        obtain the actual list """
        ndirs = []
        if dirs == None: # default entries
            ndirs = glob.glob ( "_V*" )
            ndirs += glob.glob ( "tmp*" )
        if type(dirs) == str: # entry with wildcards
            ndirs = [ dirs ] # single entry
            if "*" in dirs or "?" in dirs:
                ndirs = glob.glob ( dirs )
        if type(dirs) == list:
            ndirs = copy.deepcopy ( dirs )
        ret = []
        for d in ndirs:
            if d.endswith ( ".ini" ) or d.endswith ( ".py" ) or d.endswith(".png"):
                continue
            ret.append ( d )
        return ret

    def parse( self, dirs : Union[None,str,list] = None ):
        """ parse for directories
        :param dirs: if None, look for _V* and tmp* directories, else
        consider only the directories given.
        """
        if dirs == None:
            dirs = self.dirs
        ndirs = self.getDirs ( dirs )

        ctr = 0
        while len(ndirs)==0:
            t = (2.+ctr)**2
            if not self.waitForDirs: 
                return # asked to _not_ wait
            print ( f"[progress] could not find any usual directories. will wait for {t:.0f}s" )
            ctr+=1
            time.sleep ( t )
            if ctr>10:
                print ( f"[progress] waited enough, lets terminate." )
                sys.exit()
            # refresh the list of dirs
            ndirs = self.getDirs ( dirs )
            sys.exit()
        ret = {}
        for d in ndirs:
            npoints = len ( glob.glob ( f"{d}/T*slha" ) )
            ndone = len ( glob.glob ( f"{d}/results/T*.py" ) )
            ret[d]= { "npoints": npoints, "ndone": ndone }
        self.previous = self.stats
        self.stats = ret

    def pprint ( self ):
        print ( "[progress] stats", self.stats )

    def updateTQDM ( self, name : str, values : Dict, position : int ):
        """ update an entry in self.tqdms """
        fullname = os.path.basename ( name )
        fullname = f"{fullname:10s}"
        n = tqdm ( desc=fullname, total = values["npoints"], position = position,
                   unit = "pt", bar_format="{desc}: {percentage:3.0f}%|{bar:46}| {n_fmt}/{total_fmt} [{remaining}] {postfix}", colour = "green" )
        self.tqdms[name]=n

    def show( self ):
        # self.pprint()
        self.tqdms = {}
        for i,(k,v) in enumerate ( self.stats.items() ):
            self.updateTQDM ( k, v, i )
        while True:
            time.sleep(.3)
            self.parse()
            for i,(k,v) in enumerate ( self.stats.items() ):
                if "npoints" in v and k in self.previous:
                    if "npoints" in self.previous[k]:
                        prevnpoints = self.previous[k]["npoints"]
                        if prevnpoints != v["npoints"]:
                            self.tqdms[k].reset ( v["npoints"] )
                if not k in self.tqdms:
                    if k in self.stats:
                        self.updateTQDM ( k, v, i )
                self.tqdms[k].update ( v["ndone"] - self.tqdms[k].n )


if __name__ == "__main__":
    p = Progress()

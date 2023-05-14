#!/usr/bin/env python3

import glob, time
from tqdm import tqdm

class Progress:
    def __init__ ( self ):
        self.show()

    def parse( self ):
        dirs = glob.glob ( "_V*" )
        dirs += glob.glob ( "tmp*" )
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
        self.pprint()
        self.tqdms = []
        for i,(k,v) in enumerate ( self.stats.items() ):
            n = tqdm ( total = v["npoints"], position = i, )# \
            #           initial = v["ndone"] )
            self.tqdms.append ( n )
        while True:
            time.sleep(.3)
            self.parse()
            for i,(k,v) in enumerate ( self.stats.items() ):
                self.tqdms[i].update ( v["ndone"] - self.tqdms[i].n )


if __name__ == "__main__":
    p = Progress()

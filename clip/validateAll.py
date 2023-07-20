#!/usr/bin/env python3

""" a script that is meant to write a script to submit jobs
    for all validations possible """
        
import glob, os

class Validator:
    def __init__ ( self ):
        home = os.environ["HOME"]
        self.dbpath = f"{home}/git/smodels-database"
        self.commandsfile = "commands.sh"
        self.f = open ( self.commandsfile, "wt" )
        self.f.write ( "#!/bin/sh\n\n" )

    def find( self ):
        res = []
        for tev in glob.glob ( f"{self.dbpath}/*TeV" ):
            for exp in glob.glob ( f"{tev}/*" ):
                for result in glob.glob ( f"{exp}/*" ):
                    res.append ( result )
        def sorter ( x ):
            h = hash(x)
            if x.endswith("-eff"):
                h = -abs(h) -1e19
            return h
        res.sort ( key = sorter )
        return res

    def getTopos ( self, folder : str ) -> set:
        ret = set()
        cands = glob.glob ( f"{folder}/*/T*.txt" )
        for cand in cands:
            c = os.path.basename ( cand )
            c = c.replace(".txt","")
            ret.add ( c )
        return ret

    def write ( self, line : str ):
        print ( line )
        self.f.write ( line + "\n" )

    def writeSingleTopo ( self, topo, ana, anaType ):
        # print ( "ana", ana, "topo", topo, "type", anaType )
        exe="./slurm.py"
        inifile = "combined_1cpu.ini"
        if anaType == "UL":
            inifile = "ul.ini"
        cmd = f"{exe} -V {inifile} -a {ana} -T {topo}"
        self.write ( cmd )
        if anaType == "combined":
            inifile = "effmaps.ini"
            cmd = f"{exe} -V {inifile} -a {ana} -T {topo}"
            self.write ( cmd )

    def close ( self ):
        self.f.close()
        os.chmod ( self.commandsfile, 0o755 )

    def run( self ):
        anas = self.find()
        for ana in anas:
            topos = self.getTopos ( ana )
            mana = os.path.basename ( ana )
            anaType = "UL"
            if mana.endswith ( "-eff" ):
                anaType = "combined"
                mana = mana.replace("-eff","")
            for t in topos:
                self.writeSingleTopo ( t, mana, anaType )
        self.close()

if __name__ == "__main__":
    v = Validator()
    v.run()

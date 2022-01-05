#!/usr/bin/env python3

""" a separate facility to combine validation plots. We do not bother
    here with creating the .py files, we assume they are already produced """

import os
import sys
sys.path.insert(0,"../")
from smodels_utils.helper.various import getPathName
from validationHelpers import getValidationFileContent, shortTxName

class ValidationCombiner:
    def __init__ ( self, databasePath : str, anaId : str, txdicts : list,
                         xrange, yrange ):
        """
        param txdicts: list of txnames to combine, e.g.
        [ "TChiWZ_2EqMassAx_EqMassBy_combined.py",
          "TChiWZoff_2EqMassAx_EqMassBy_combined.py" ]
        :param xrange: either None, or string, e.g. "[0,200]"
        :param yrange: either None, or string, e.g. "[0,200]"
        """
        self.databasePath = databasePath
        self.xrange = eval(str(xrange))
        self.yrange = eval(str(yrange))
        self.anaId = anaId
        self.txdicts = txdicts
        self.getValNames()
        self.greet()
        self.read()
        self.getExclusions()
        self.plot()

    def passesRanges ( self, d ):
        """ check if data 'd' passes all the ranges """
        if not "axes" in d:
            return True
        if self.xrange != None:
            if d["axes"]["x"] > self.xrange[1]:
                return False
            if d["axes"]["x"] < self.xrange[0]:
                return False
        if self.yrange != None:
            if d["axes"]["y"] > self.yrange[1]:
                return False
            if d["axes"]["y"] < self.yrange[0]:
                return False
        return True

    def read ( self ):
        """ read in the data from the various sources """
        self.data = []
        self.meta = {}
        for txname,v in self.validationFiles.items():
            fname = getPathName ( self.databasePath, self.anaId, v )
            content = getValidationFileContent ( fname )
            self.meta[txname]=content["meta"]
            for d in content["data"]:
                if self.passesRanges ( d ):
                    self.data.append ( d )

    def txShort ( self ):
        """ get a short moniker for the txnames """
        return shortTxName ( self.validationFiles.keys() )

    def getExclusions ( self ):
        self.exclusions = {}
        from smodels_utils.helper.uprootTools import getExclusionLine
        path = getPathName ( self.databasePath, self.anaId, None )
        axes = "[[x, y], [x, y]]"
        for pm in [ "", "M1", "P1" ]:
            for expected in [ True, False ]:
                ret = { "x": [], "y": [] }
                for txname,v in self.validationFiles.items():
                    if self.meta == None:
                       print ( "[combineValidation.py] no meta info. trying with default axes" )
                    else:
                        axes = self.meta[txname]["axes"]
                    line = getExclusionLine ( path, txname, axes = axes,
                           expected = expected, pm = pm, verbose=False )
                    if type(line) != dict:
                        continue
                    if not "x" in line:
                        continue
                    if len(line["x"])==0:
                        # print ( f"[combineValidation] found exclusion line for {txname} with no entries" )
                        continue
                    # print ( f'[combineValidation] {txname}: exclusion line with {len(line["x"])} points' )
                    for x,y in zip ( line["x"], line["y"] ):
                        ret["x"].append ( x )
                        ret["y"].append ( y )
                sname = "obs"+pm
                if expected:
                    sname = "exp"+pm
                self.exclusions[sname] = ret

    def plot ( self ):
        from smodels_utils.plotting import mpkitty as plt
        # import matplotlib.pyplot as plt ## for non-kitty version
        idNoEff= self.anaId.replace("-eff","")
        x, y, r, ex, ey, nx, ny = [], [], [], [], [], [], []
        for row in self.data:
            try:
                xi = row["axes"]["x"]
                yi = row["axes"]["y"]
                ri = row["signal"] / row["UL"]
                x.append ( xi )
                y.append ( yi )
                r.append ( ri )
                if ri > 1.:
                    ex.append ( xi )
                    ey.append ( yi )
                else:
                    nx.append ( xi )
                    ny.append ( yi )
            except KeyError as e:
                pass
            except TypeError as e:
                pass
        import matplotlib
        plt.scatter ( ex, ey, c="r", s=90. )
        plt.scatter ( nx, ny, c="g", s=90. )
        #cmap = "Blues"
        #cmap = "gray"
        cmap = "bone"
        plt.scatter ( x, y, c=r, s=20., norm=matplotlib.colors.LogNorm(), 
                      cmap=cmap, alpha=1. )
        cbar = plt.colorbar()
        cbar.set_label ( "r" )
        plt.title ( f"{idNoEff}, {self.txShort()}" )
        plt.xlabel ( "x [GeV]" )
        plt.ylabel ( "y [GeV]" )
        if "obs" in self.exclusions:
            plt.plot ( self.exclusions["obs"]["x"],self.exclusions["obs"]["y"],
                       c="k", linewidth=2 )
        axes = ""
        for txname,meta in self.meta.items():
            axes = meta["axes"].replace(" ","")
        fname = f"combo_{idNoEff}_{self.txShort()}_{axes}.png"
        fname = fname.replace("[","").replace("]","").replace("*","").replace(",","")
        plt.savefig ( fname )
        plt.kittyPlot()
        print ( f"[combineValidation] saving to {fname}" )

    def greet ( self ):
        print (f"[ValidationCombiner] combining {self.anaId}, {self.databasePath}:")
        for k,v in self.validationFiles.items():
            print ( f"           --- '{k}': {v}" )

    def getValNames ( self ):
        self.validationFiles = {}
        for i in self.txdicts.split(","):
            t = i.strip()
            p1 = t.find("_")
            txname = t[:p1]
            self.validationFiles[txname]= t


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Produces combined validation plots, of aon- and offshell regions")
    ap.add_argument('-d', '--database',
            help='path to database [../../smodels-database]', type=str,
            default='../../smodels-database/')
    ap.add_argument('-a', '--analysisId',
            help='analysis id [ATLAS-SUSY-2018-06-eff]', type=str,
            default='ATLAS-SUSY-2018-06-eff')
    ap.add_argument('-x', '--xrange',
            help='user-specified x-range, e.g. "[0,200]" [None]', type=str,
            default=None )
    ap.add_argument('-y', '--yrange',
            help='user-specified y-range, e.g. "[0,200]" [None]', type=str,
            default=None )
    ap.add_argument('-v', '--validationfiles',
            help='validation files, comma separated [TChiWZoff_2EqMassAx_EqMassBy.py, TChiWZ_2EqMassAx_EqMassBy.py]',
            type=str, default='TChiWZoff_2EqMassAx_EqMassBy.py, TChiWZ_2EqMassAx_EqMassBy.py')

    args = ap.parse_args()
    plotter = ValidationCombiner ( args.database, args.analysisId, 
            args.validationfiles, args.xrange, args.yrange )

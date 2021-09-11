#!/usr/bin/env python3

""" a separate facility to combine validation plots. We do not bother
    here with creating the .py files, we assume they are already produced """

import os
from smodels_utils.helper.various import getPathName
from validationHelpers import getValidationFileContent, shortTxName

class ValidationCombiner:
    def __init__ ( self, databasePath : str, anaId : str, txdicts : list ):
        """
        param txdicts: list of txnames to combine, e.g.
        [ "TChiWZ_2EqMassAx_EqMassBy_combined.py",
          "TChiWZoff_2EqMassAx_EqMassBy_combined.py" ]
        """
        self.databasePath = databasePath
        self.anaId = anaId
        self.txdicts = txdicts
        self.getValNames()
        self.greet()
        self.read()
        self.getExclusions()
        self.plot()

    def read ( self ):
        """ read in the data from the various sources """
        self.data = []
        self.meta = {}
        for txname,v in self.validationFiles.items():
            fname = getPathName ( self.databasePath, self.anaId, v )
            content = getValidationFileContent ( fname )
            self.meta[txname]=content["meta"]
            for d in content["data"]:
                self.data.append ( d )

    def txShort ( self ):
        """ get a short moniker for the txnames """
        return shortTxName ( self.validationFiles.keys() )

    def getExclusions ( self ):
        self.exclusions = {}
        from smodels_utils.helper.uprootTools import getExclusionLine
        path = getPathName ( self.databasePath, self.anaId, None )
        for pm in [ "", "M1", "P1" ]:
            for expected in [ True, False ]:
                ret = { "x": [], "y": [] }
                for txname,v in self.validationFiles.items():
                    axes = "[[x, y], [x, y]]"
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
        plt.scatter ( x, y, c=r, s=20., norm=matplotlib.colors.LogNorm(), 
                      cmap="gray", alpha=1. )
        cbar = plt.colorbar()
        cbar.set_label ( "r" )
        plt.title ( f"{idNoEff}, {self.txShort()}" )
        plt.xlabel ( "x [GeV]" )
        plt.ylabel ( "y [GeV]" )
        if "obs" in self.exclusions:
            plt.plot ( self.exclusions["obs"]["x"],self.exclusions["obs"]["y"],
                       c="k", linewidth=2 )
        fname = f"combo_{idNoEff}_{self.txShort()}.png"
        print ( f"[combineValidation] saving to {fname}" )
        plt.savefig ( fname )
        plt.show()

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
    ap.add_argument('-v', '--validationfiles',
            help='validation files, comma separated [TChiWZoff_2EqMassAx_EqMassBy.py, TChiWZ_2EqMassAx_EqMassBy.py]',
            type=str, default='TChiWZoff_2EqMassAx_EqMassBy.py, TChiWZ_2EqMassAx_EqMassBy.py')

    args = ap.parse_args()
    plotter = ValidationCombiner ( args.database, args.analysisId, args.validationfiles )

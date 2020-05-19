#!/usr/bin/env python3

""" a simple class that performs global modifications on a list of results.
Used to ``take out potential signals'' i.e. put all observations to values
expected from background, by sampling the background model. """

from scipy import stats

class ExpResModifier:
    def __init__ ( self, modificationType = "expected" ):
        self.modificationType = modificationType

    def interact ( self, listOfExpRes ):
        import IPython
        IPython.embed()

    def fixUpperLimit ( self, dataset ):
        for txname in dataset.txnameList:
            if hasattr ( txname, "txnameDataExp" ):
                print ( "[expResModifier] fixing UL result %s" % dataset.globalInfo.id )
                txname.txnameData = txname.txnameDataExp
        return dataset

    def fixEfficiencyMap ( self, dataset ):
        orig = dataset.dataInfo.observedN
        exp = dataset.dataInfo.expectedBG
        err = dataset.dataInfo.bgError
        lmbda = stats.norm.rvs ( exp, err )
        if lmbda < 0.:
            lmbda = 0.
        obs = stats.poisson.rvs ( lmbda )
        print ( "[expResModifier] effmap replacing nobs=%.2f by nobs=%.2f for %s" % \
                ( orig, obs, dataset.globalInfo.id ) )
        dataset.dataInfo.observedN = obs
        dataset.dataInfo.origN = orig
        return dataset

    def modify ( self, listOfExpRes ):
        ret = []
        for expRes in listOfExpRes:
            for ids,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                if dt == "upperLimit":
                    self.fixUpperLimit ( dataset )
                elif dt == "efficiencyMap":
                    self.fixEfficiencyMap ( dataset )
                else:
                    print ( "[expResModifier] dataset type %s unknown" % dt )
                
            ret.append ( expRes )
        return ret

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
                        description='experimental results modifier. used to take out potential signals from the database by setting all observations to values sampled from the background expectations' )
    argparser.add_argument ( '-d', '--database',
            help='database to use [../../smodels/test/database]',
            type=str, default="../../smodels/test/database" )
    argparser.add_argument ( '-o', '--outfile',
            help='file to write out database pickle [""]',
            type=str, default="" )
    argparser.add_argument ( '-v', '--verbose',
            help='print results to stdout', action='store_true' )
    argparser.add_argument ( '-i', '--interact',
            help='interactive mode', action='store_true' )
    args = argparser.parse_args()
    from smodels.experiment.databaseObj import Database
    db = Database ( args.database )
    listOfExpRes = db.getExpResults()
    modifier = ExpResModifier()
    updatedListOfExpRes = modifier.modify ( listOfExpRes )
    db.expResultList = updatedListOfExpRes
    print ( "Modifier called. %d/%d results" % \
            ( len(updatedListOfExpRes), len(listOfExpRes) ) )
    if args.outfile != "":
        db.createBinaryFile( args.outfile )

    if args.interact:
        modifier.interact ( listOfExpRes )

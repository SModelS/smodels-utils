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
        return dataset

    def fixEfficiencyMap ( self, dataset ):
        orig = dataset.dataInfo.observedN
        exp = dataset.dataInfo.expectedBG
        err = dataset.dataInfo.bgError
        lmbda = stats.norm.rvs ( exp, err )
        if lmbda < 0.:
            lmbda = 0.
        obs = stats.poisson.rvs ( lmbda )
        print ( "[expResModifier] replacing %.2f by %.2f" % ( orig, obs ) )
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
            help='database to use [../../smodels-database]',
            type=str, default="../../smodels/test/database" )
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
    print ( "Modifier called. %d/%d results" % \
            ( len(updatedListOfExpRes), len(listOfExpRes) ) )
    if args.interact:
        modifier.interact ( listOfExpRes )

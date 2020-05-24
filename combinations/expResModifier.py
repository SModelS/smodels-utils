#!/usr/bin/env python3

""" a simple class that performs global modifications on a list of results.
Used to ``take out potential signals'' i.e. put all observations to values
expected from background, by sampling the background model. """

import copy
from scipy import stats

class ExpResModifier:
    def __init__ ( self, modificationType = "expected" ):
        self.modificationType = modificationType

    def interact ( self, listOfExpRes ):
        import IPython
        IPython.embed()

    def fixUpperLimit ( self, dataset ):
        for i,txname in enumerate(dataset.txnameList):
            if hasattr ( txname, "txnameDataExp" ) and txname.txnameDataExp != None:
                print ( "[expResModifier] fixing UL result %s" % dataset.globalInfo.id )
                txnd = copy.deepcopy ( txname.txnameDataExp ) 
                dataset.txnameList[i].txnameData = txnd
        return dataset

    def modifyDatabase ( self, db, outfile="", suffix="fake1" ):
        """ modify the database 
        :param outfile: if not empty, write the database into file
        :param suffix: suffix to append to database version
        """
        listOfExpRes = db.getExpResults()
        updatedListOfExpRes = self.modify ( listOfExpRes )
        db.expResultList = updatedListOfExpRes
        newver = db.databaseVersion + suffix
        db.txt_meta.databaseVersion = newver
        db.pcl_meta.databaseVersion = newver
        print ( "Modifier called. %d/%d results" % \
                ( len(updatedListOfExpRes), len(listOfExpRes) ) )
        if outfile != "":
            db.createBinaryFile( outfile )
        return db

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
            for i,dataset in enumerate(expRes.datasets):
                dt = dataset.dataInfo.dataType
                if dt == "upperLimit":
                    expRes.datasets[i] = self.fixUpperLimit ( dataset )
                elif dt == "efficiencyMap":
                    expRes.datasets[i] = self.fixEfficiencyMap ( dataset )
                else:
                    print ( "[expResModifier] dataset type %s unknown" % dt )
                
            ret.append ( expRes )
        return ret

def check ( picklefile ):
    """ check the picklefile """
    print ( "now checking the modified database" )
    db = Database ( picklefile )
    listOfExpRes = db.getExpResults()
    for er in listOfExpRes:
        datasets = er.datasets
        for ds in datasets:
            txnl = ds.txnameList
            for txn in txnl:
                x = txn.txnameData.dataType
    print ( "were good", db.databaseVersion )


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
                        description='experimental results modifier. used to take out potential signals from the database by setting all observations to values sampled from the background expectations' )
    argparser.add_argument ( '-d', '--database',
            help='database to use [../../smodels-database]',
            type=str, default="../../smodels-database" )
    argparser.add_argument ( '-o', '--outfile',
            help='file to write out database pickle [""]',
            type=str, default="" )
    argparser.add_argument ( '-s', '--suffix',
            help='suffix for database version ["fake1"]',
            type=str, default="fake1" )
    argparser.add_argument ( '-v', '--verbose',
            help='print results to stdout', action='store_true' )
    argparser.add_argument ( '-i', '--interact',
            help='interactive mode', action='store_true' )
    argparser.add_argument ( '-c', '--check',
            help='check the pickle file <outfile>', action='store_true' )
    args = argparser.parse_args()
    from smodels.experiment.databaseObj import Database
    db = Database ( args.database )
    modifier = ExpResModifier()
    modifier.modifyDatabase ( db, args.outfile, args.suffix )

    if args.check:
        check ( args.outfile )

    if args.interact:
        modifier.interact ( listOfExpRes )

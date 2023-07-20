#!/usr/bin/env python

"""
.. module:: rootPrinter
   :synopsis: A class that prints into a ROOT file

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging
from smodels.theory.topology import TopologyList
from smodels.theory.element import Element
from smodels.theory.theoryPrediction import TheoryPredictionList, theoryPredictionsFor
from smodels.experiment.txnameObj import TxName
from smodels.tools.ioObjects import OutputStatus, ResultList
from smodels.tools.missingTopos import MissingTopoList
from smodels.base.physicsUnits import GeV, fb, TeV, pb
from smodels.experiment.databaseObjects import Database
import ROOT

logger = logging.getLogger(__name__)
logger.setLevel ( logging.DEBUG )

class ROOTPrinter(object):
    """
    Printer class to handle the printing of one single output to a root file
    """

    def prepareTheoryNr ( self ):
        ROOT.gROOT.ProcessLine ( \
                "struct TheoryNr{ \
                    int theory_nr;\
                 };" )
        self.TheoryNr = ROOT.TheoryNr()
        self.TheoryNr.theory_nr = 0

    def prepareElements ( self ):
        """ prepare the ttree for the elements """
        if self.hasPreparedElements:
            return
        self.hasPreparedElements=True
        self.elements=ROOT.TTree ( "elements", "elements" )
        self.elements_particles = ROOT.std.vector(ROOT.std.string)()
        self.elements_masses = ROOT.std.vector(ROOT.std.string)()
        self.elements_weight_pb = ROOT.std.vector(float)()
        self.elements_mother_0_pid = ROOT.std.vector(int)()
        self.elements_mother_1_pid = ROOT.std.vector(int)()
        self.elements_mother_0_mass = ROOT.std.vector(float)()
        self.elements_mother_1_mass = ROOT.std.vector(float)()
        self.elements_pids = ROOT.std.vector(ROOT.std.string)()
        self.elements_sqrts = ROOT.std.vector(ROOT.std.string)()
        self.elements.Branch ( "theory_nr", ROOT.AddressOf ( self.TheoryNr, "theory_nr" ), "theory_nr/I" )
        self.elements.Branch ( "particles", self.elements_particles )
        self.elements.Branch ( "masses", self.elements_masses )
        self.elements.Branch ( "weight_pb", self.elements_weight_pb )
        self.elements.Branch ( "mother_0_pid", self.elements_mother_0_pid )
        self.elements.Branch ( "mother_1_pid", self.elements_mother_1_pid )
        self.elements.Branch ( "mother_0_mass", self.elements_mother_0_mass )
        self.elements.Branch ( "mother_1_mass", self.elements_mother_1_mass )
        self.elements.Branch ( "pids", self.elements_pids )
        self.elements.Branch ( "sqrts", self.elements_sqrts )

    def prepareOutputStatus ( self ):
        """ prepare the ttree for the output status """
        if self.hasPreparedOutputStatus:
            return
        self.hasPreparedOutputStatus=True
        ROOT.gROOT.ProcessLine ( \
                "struct OutputStatus{ \
                    int filestatus;\
                    char inputfile[256];\
                    char outputfile[256];\
                    char databaseVersion[256];\
                    char warnings[512];\
                 };" )
        self.outputstatus_databaseVersion = ROOT.std.string() 
        self.OutputStatus = ROOT.OutputStatus()
        self.OutputStatusTree = ROOT.TTree ( "OutputStatus", "OutputStatus" )
        self.OutputStatusTree.Branch ( "filestatus", ROOT.AddressOf ( self.OutputStatus, "filestatus" ), "filestatus/I" )
        self.OutputStatusTree.Branch ( "outputfile", ROOT.AddressOf ( self.OutputStatus, "outputfile" ), "outputfile/C" )
        self.OutputStatusTree.Branch ( "inputfile", ROOT.AddressOf ( self.OutputStatus, "inputfile" ), "inputfile/C" )
        self.OutputStatusTree.Branch ( "warnings", ROOT.AddressOf ( self.OutputStatus, "warnings" ), "warnings/C" )
        self.OutputStatusTree.Branch ( "databaseVersion", ROOT.AddressOf ( self.OutputStatus, "databaseVersion" ), "databaseVersion/C" )
        self.OutputStatusTree.Branch ( "theory_nr", ROOT.AddressOf ( self.TheoryNr, "theory_nr" ), "theory_nr/I" )


    def prepareMissingTopos ( self ):
        """ prepare the ttree for missing topologies """
        if self.hasPreparedMissingTopos:
            return
        self.hasPreparedMissingTopos=True
        self.missingtopos=ROOT.TTree ( "missingtopos", "missingtopos" )
        self.missingtopos_topo = ROOT.std.vector ( ROOT.std.string) ()
        self.missingtopos_weights= ROOT.std.vector ( ROOT.std.string) ()
        self.missingtopos_value = ROOT.std.vector ( float ) ()
        self.missingtopos.Branch ( "theory_nr", ROOT.AddressOf ( self.TheoryNr, "theory_nr" ), "theory_nr/I" )
        self.missingtopos.Branch ( "topo", self.missingtopos_topo )
        self.missingtopos.Branch ( "weights", self.missingtopos_weights )
        self.missingtopos.Branch ( "value", self.missingtopos_value )

    def prepareTheoryPredictions ( self ):
        """ prepare a ttree for theory predictions """
        if self.hasPreparedTheoryPredictions:
            return
        self.hasPreparedTheoryPredictions=True
        self.theorypredictions=ROOT.TTree ( "theorypredictions", "theorypredictions" )
        self.theorypred_experimental_id = ROOT.std.vector ( ROOT.std.string )()
        self.theorypred_txname = ROOT.std.vector ( ROOT.std.string )()
        self.theorypred_dataset = ROOT.std.vector ( ROOT.std.string )()
        self.theorypred_masses = ROOT.std.vector ( ROOT.std.string )()
        self.theorypred_value_pb = ROOT.std.vector ( float )()
        self.theorypred_exp_ul_pb = ROOT.std.vector ( float )()
        self.theorypred_cond_violation = ROOT.std.vector ( float )()
        self.theorypredictions.Branch ( "experimental_id", self.theorypred_experimental_id )
        self.theorypredictions.Branch ( "value_pb", self.theorypred_value_pb )
        self.theorypredictions.Branch ( "masses", self.theorypred_masses )
        self.theorypredictions.Branch ( "exp_ul_pb", self.theorypred_exp_ul_pb )
        self.theorypredictions.Branch ( "cond_violation", self.theorypred_cond_violation )
        self.theorypredictions.Branch ( "theory_nr", ROOT.AddressOf ( self.TheoryNr, "theory_nr" ), "theory_nr/I" )
        self.theorypredictions.Branch ( "txname", self.theorypred_txname )
        self.theorypredictions.Branch ( "dataset", self.theorypred_dataset )

    def __init__(self, filename = "out.root" ):
        self.objList = []
        self.outputLevel = 1
        self.filename = filename
        self.element_ctr = 0
        self.theory_nr = 0
        logger.debug ( "__init__" )
        self.prepareTheoryNr()
        self.hasPreparedTheoryPredictions=False
        self.hasPreparedElements=False
        self.hasPreparedMissingTopos=False
        self.hasPreparedOutputStatus=False

    def writeElement ( self, element ):
        self.prepareElements()
        logger.debug ( "write element %s" % element )
        logger.debug ( "write element particles %s" % element.getParticles() )
        logger.debug ( "element weight=%s" % element.weight.getDictionary() )
        self.elements_particles.push_back ( str ( element.getParticles() ) )
        self.elements_masses.push_back ( str ( element.getMasses() ) )
        self.elements_mother_0_mass.push_back ( element.getMasses()[0][0].asNumber ( GeV) )
        self.elements_mother_1_mass.push_back ( element.getMasses()[1][0].asNumber ( GeV) )
        weight = float("nan")
        mother_0_pid, mother_1_pid = None, None
        sqrts="?"
        for ( pids,value ) in element.weight.getDictionary().items():
            for ( sqrts, value_pb ) in value.items():
                weight=value_pb.asNumber(pb)
                mother_0_pid = pids[0]
                mother_1_pid = pids[1]
                sqrts = sqrts
        self.elements_weight_pb.push_back ( weight )
        if mother_0_pid == None:
            mother_0_pid = 0
        self.elements_mother_0_pid.push_back ( mother_0_pid )
        if mother_1_pid == None:
            mother_1_pid = 0
        self.elements_mother_1_pid.push_back ( mother_1_pid )
        self.elements_pids.push_back ( str ( element.getPIDs() ) )
        self.elements_sqrts.push_back ( sqrts )

    def writeTopology ( self, topology ):
        logger.debug ( "write elements of topology %s" % topology )
        for element in topology.elementList:
            self.writeElement ( element )

    def writeTopologyList ( self, topolist ):

        for topology in topolist:
            self.writeTopology ( topology )

        self.element_ctr += 1


    def writeTheoryPrediction ( self, obj, expResult, datasetInfo ):
        self.prepareTheoryPredictions()
        logger.info ( "write theory prediction for %s" % expResult.info.getMetaData("id") )
        logger.info ( "theory prediction for %s" % obj.analysis )
        logger.info ( "theory prediction for txname %s" % obj.txname )
        self.theorypred_txname.push_back ( str(obj.txname) )
        self.theorypred_dataset.push_back ( str(datasetInfo.getValuesFor('dataid')) )
        #logger.info ( "theory prediction for dataset %s" % expResult.dataset.getValuesFor('dataid') )
        #self.theorypred_dataset.push_back ( obj.dataset.getValuesFor('dataid') )
        logger.info ( "theory value %s " % obj.value )
        self.theorypred_experimental_id.push_back ( expResult.info.getMetaData("id")  )
        self.theorypred_masses.push_back ( str(obj.mass) )
        exp_ul=float('nan')
        if expResult.getValuesFor('datatype') == 'upper-limit':
            exp_ul=expResult.getUpperLimitFor(txname=obj.txname,mass=obj.mass)
        else:
            exp_ul = expRes.getUpperLimitFor(dataID=datasetInfo.dataid)
        if type(exp_ul) == type(None):
            exp_ul = float('nan' )
        else:
            exp_ul = exp_ul.asNumber ( pb )
        self.theorypred_exp_ul_pb.push_back ( exp_ul )
        value_pb=float("nan")
        logger.info ( "xsections %s" % str ( obj.value.getDictionary() ) )
        conds=float("nan")
        #print "conditions =", obj.conditions
        if obj.conditions:
            conds=max ( obj.conditions.values() )
        self.theorypred_cond_violation.push_back ( conds )
        for (pids, sqrtsvalue ) in obj.value.getDictionary().items():
            logger.info ( "pids=%s sqrtsvalue=%s" % ( pids, sqrtsvalue ) )
            for (sqrts, value ) in sqrtsvalue.items():
                self.theorypred_value_pb.push_back ( value.asNumber(pb) )



    def writeTheoryPredictionList ( self, obj ):
        logger.info ( "write theory predictionlist" )
        logger.info ( "theory prediction list for dataid %s" % obj.dataset.getValuesFor('dataid') )
        logger.info ( "theory prediction list for dataset %s" % obj.dataset )
        logger.info ( "theory prediction list for experimental result %s" % obj.expResult )
        logger.info ( "theory prediction list for experimental result %s" % obj.expResult.info.getMetaData("id") )
        for theoryprediction in obj:
            self.writeTheoryPrediction ( theoryprediction, obj.expResult, obj.dataset )
        logger.info ( "done writing theory prediction list" )

    def writeMissingTopo ( self, obj ):
        self.prepareMissingTopos()
        logger.info ( "write missing topo %s" % obj )
        self.missingtopos_topo.push_back ( obj.topo )
        self.missingtopos_weights.push_back ( str(obj.weights) )
        self.missingtopos_value.push_back ( obj.value )

    def writeMissingTopos ( self, obj ):
        logger.info ( "writing missing topologies %s" % obj )
        for i in obj.topos:
            self.writeMissingTopo ( i )

    def writeOutputStatus ( self, obj ):
        self.prepareOutputStatus()
        self.OutputStatus.filestatus = obj.filestatus
        if len(obj.outputfile)>255:
                logger.error ( "outputfile string is too long" )
        self.OutputStatus.outputfile = obj.outputfile
        if len(obj.inputfile)>255:
                logger.error ( "inputfile string is too long" )
        self.OutputStatus.inputfile = obj.inputfile
        if len(obj.databaseVersion)>255:
                logger.error ( "databaseVersion string is too long" )
        self.OutputStatus.databaseVersion = obj.databaseVersion
        if len(str(obj.warnings))>511:
                logger.error ( "warnings string is too long" )
        self.OutputStatus.warnings = str(obj.warnings)

    def write ( self, obj ):
        """ write any type of object """
        logger.info( "now printing %s" % str(obj ) )
        if isinstance ( obj, TopologyList ):
            self.writeTopologyList ( obj )
        elif isinstance ( obj, TheoryPredictionList ):
            self.writeTheoryPredictionList ( obj )
        elif isinstance ( obj, MissingTopoList ):
            self.writeMissingTopos ( obj )
        elif isinstance ( obj, OutputStatus ):
            self.writeOutputStatus ( obj )
        elif isinstance ( obj, list ):
            for i in obj:
                self.write ( i )
        else:
            logger.error ( "dont know yet how to handle %s types." % type(obj) )

    def close(self):
        """
        Closes the printer and print the objects added to the output defined
        """
        logger.info ( "close")
        if not self.filename:
            return
        self.rootfile=ROOT.TFile( self.filename, "recreate" )
        for obj in self.objList:
            self.write ( obj )
        self.flush()
        if self.hasPreparedMissingTopos:
            self.missingtopos.Write()
        if self.hasPreparedElements:
            self.elements.Write()
        if self.hasPreparedTheoryPredictions:
            self.theorypredictions.Write()
        if self.hasPreparedOutputStatus:
            self.OutputStatusTree.Write()
        self.rootfile.Close()
        logger.info


    def addObj(self,obj,outputLevel=None):
        """
        Adds object to the Printer. The object will formatted according to the outputType
        and the outputLevel. The resulting output will be stored in outputList.
        :param obj: A object to be printed. Must match one of the types defined in formatObj
        :param outputlevel: currently not used
        """
        logger.debug ( "addObj %s" % type(obj) )
        self.objList.append(obj)

    def flush(self, theory_nr = None):
        """
        tells the printer that the next theory point is being processed
        """
        if theory_nr:
            self.TheoryNr.theory_nr= theory_nr
        logger.info ("next theory point" )
        if self.hasPreparedElements:
            self.elements.Fill()
            self.elements_particles.clear()
            self.elements_masses.clear()
            self.elements_weight_pb.clear()
            self.elements_mother_0_pid.clear()
            self.elements_mother_1_pid.clear()
            self.elements_mother_0_mass.clear()
            self.elements_mother_1_mass.clear()
            self.elements_sqrts.clear()

        if self.hasPreparedTheoryPredictions:
            self.theorypredictions.Fill()
            self.theorypred_experimental_id.clear()
            self.theorypred_txname.clear()
            self.theorypred_dataset.clear()
            self.theorypred_masses.clear()
            self.theorypred_value_pb.clear()
            self.theorypred_exp_ul_pb.clear()
            self.theorypred_cond_violation.clear()

        if self.hasPreparedMissingTopos:
            self.missingtopos.Fill()
            self.missingtopos_topo.clear()
            self.missingtopos_weights.clear()
            self.missingtopos_value.clear()

        if self.hasPreparedOutputStatus:
            self.OutputStatusTree.Fill()

        if not theory_nr:
            self.TheoryNr.theory_nr+=1


if __name__ == "__main__":
    from smodels.installation import installDirectory
    slhafile = installDirectory() + '/inputFiles/slha/lightEWinos.slha'
    ## slhafile = installDirectory() + '/inputFiles/slha/gluino_squarks.slha'
    sigmacut = 0.1 *fb
    mingap = 5* GeV

    outputstats = OutputStatus([1,None], slhafile,  
         {'sigmacut' : sigmacut, 'mingap' : mingap}, '1.0.90','outputfile') 
    printer = ROOTPrinter("out.root")

    printer.addObj ( outputstats)
    print "slhafile=",slhafile
    from smodels.theory import slhaDecomposer
    smstoplist = slhaDecomposer.decompose(slhafile, sigcut=sigmacut, minmassgap=mingap )
    printer.addObj ( smstoplist )

    # database = Database ( installDirectory() + '/test/database' )
    database = Database ( "../../../smodels-database" )
    listOfExpRes = database.getExpResults(datasetIDs=[None])
    if type ( listOfExpRes ) != list:
        listOfExpRes = [ listOfExpRes ]
    for expResult in listOfExpRes:
        predictions = theoryPredictionsFor(expResult, smstoplist)
        if not predictions: continue
        print "[rootPrinter] addObj",predictions
        printer.addObj ( predictions )

    sqrts = max([xsec.info.sqrts for xsec in smstoplist.getTotalWeight()])
    missingtopos = MissingTopoList(sqrts)
    missingtopos.findMissingTopos(smstoplist, listOfExpRes, 5*GeV, True, True )

    printer.addObj ( missingtopos )
    printer.close()


"""
.. module:: rootPrinter
   :synopsis: A class that prints into a ROOT file

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging
from smodels.theory.topology import TopologyList
from smodels.theory.element import Element
from smodels.theory.theoryPrediction import TheoryPredictionList
from smodels.experiment.txnameObject import TxName
from smodels.tools.ioObjects import OutputStatus, ResultList
from smodels.tools.missingTopologies import MissingTopoList
from smodels.tools.physicsUnits import GeV, fb, TeV, pb
import ROOT

logger = logging.getLogger(__name__)
logger.setLevel ( logging.DEBUG )

class ROOTPrinter(object):
    """
    Printer class to handle the printing of one single output to a root file
    """
    def __init__(self, filename = "out.root" ):
        self.objList = []
        self.outputLevel = 1
        self.filename = filename
        self.element_ctr = 0
        self.event_nr = 0
        #ROOT.gROOT.ProcessLine ( \
        #        "struct Elements{ \
        #            int nr;\
        #         };" )
        logger.debug ( "__init__" )
        self.elements=ROOT.TTree ( "elements", "elements" )
        self.particles = ROOT.std.vector(ROOT.std.string)()
        self.masses = ROOT.std.vector(ROOT.std.string)()
        self.weight_pb = ROOT.std.vector(float)()
        self.mother_0_pid = ROOT.std.vector(int)()
        self.mother_1_pid = ROOT.std.vector(int)()
        self.mother_0_mass = ROOT.std.vector(float)()
        self.mother_1_mass = ROOT.std.vector(float)()
        self.sqrts = ROOT.std.vector(ROOT.std.string)()
        #self.Elements = ROOT.Elements()
        #self.Elements.nr = self.element_ctr
        #self.elements.Branch ( "nr", ROOT.AddressOf ( self.Elements, "nr" ), "nr/I" )
        self.elements.Branch ( "particles", self.particles )
        self.elements.Branch ( "masses", self.masses )
        self.elements.Branch ( "weight_pb", self.weight_pb )
        self.elements.Branch ( "mother_0_pid", self.mother_0_pid )
        self.elements.Branch ( "mother_1_pid", self.mother_1_pid )
        self.elements.Branch ( "mother_0_mass", self.mother_0_mass )
        self.elements.Branch ( "mother_1_mass", self.mother_1_mass )
        self.elements.Branch ( "sqrts", self.sqrts )

        self.theorypredictions=ROOT.TTree ( "theorypredictions", "theorypredictions" )
        self.analysis = ROOT.std.vector(ROOT.std.string)()
        self.value_pb = ROOT.std.vector(float)()
        self.theorypredictions.Branch ( "analysis", self.analysis )
        self.theorypredictions.Branch ( "value_pb", self.value_pb )

    def writeElement ( self, element ):
        logger.info ( "write element %s" % element )
        logger.info ( "write element particles %s" % element.getParticles() )
        logger.info ( "element weight=%s" % element.weight.getDictionary() )
        self.particles.push_back ( str ( element.getParticles() ) )
        self.masses.push_back ( str ( element.getMasses() ) )
        self.mother_0_mass.push_back ( element.getMasses()[0][0].asNumber ( GeV) )
        self.mother_1_mass.push_back ( element.getMasses()[1][0].asNumber ( GeV) )
        weight = float("nan")
        mother_0_pid, mother_1_pid = None, None
        sqrts="?"
        for ( pids,value ) in element.weight.getDictionary().items():
            for ( sqrts, value_pb ) in value.items():
                print "weight`",pids,sqrts,value_pb.asNumber(pb)
                weight=value_pb.asNumber(pb)
                mother_0_pid = pids[0]
                mother_1_pid = pids[1]
                sqrts = sqrts
        self.weight_pb.push_back ( weight )
        if mother_0_pid == None:
            mother_0_pid = 0
        self.mother_0_pid.push_back ( mother_0_pid )
        if mother_1_pid == None:
            mother_1_pid = 0
        self.mother_1_pid.push_back ( mother_1_pid )
        self.sqrts.push_back ( sqrts )

    def writeTopology ( self, topology ):
        logger.info ( "write topology %s" % topology )
        for element in topology.elementList:
            self.writeElement ( element )

    def writeTopologyList ( self, topolist ):

        for topology in topolist:
            self.writeTopology ( topology )
        
        self.element_ctr += 1

        self.elements.Fill()


    def writeTheoryPrediction ( self, obj ):
        logger.info ( "write theory prediction" )
        logger.info ( "theory prediction for %s" % obj.analysis )
        logger.info ( "theory value %s " % obj.value )
        self.analysis.push_back ( str(obj.analysis) )
        value_pb=float("nan")
        logger.info ( "xsections %s" % str ( obj.value.getDictionary() ) )
        ## self.value_pb.push_back ( str(obj.value.asNumber(pb)) )

    def writeTheoryPredictionList ( self, obj ):
        logger.info ( "write theory predictionlist" )
        expRes=obj.expRes
        for theoryprediction in obj:
            self.writeTheoryPrediction ( theoryprediction )
        self.theorypredictions.Fill()

    def close(self):
        """
        Closes the printer and print the objects added to the output defined
        """
        logger.info ( "close")
        if not self.filename:
            return
        self.rootfile=ROOT.TFile( self.filename, "recreate" )
        for obj in self.objList:
            logger.info( "now printing %s" % str(obj ) )
            if isinstance ( obj, TopologyList ):
                self.writeTopologyList ( obj )
#            elif isinstance ( obj, TheoryPredictionList ):
#                self.writeTheoryPredictionList ( obj )
            else:
                logger.error ( "dont know yet how to handle %s types." % type(obj) )
        self.elements.Write()
        self.theorypredictions.Write()
        self.rootfile.Close()
            
    
    def addObj(self,obj):
        """
        Adds object to the Printer. The object will formatted according to the outputType
        and the outputLevel. The resulting output will be stored in outputList.
        :param obj: A object to be printed. Must match one of the types defined in formatObj
        """
        logger.info ( "addObj %s" % type(obj) )
        self.objList.append(obj)  

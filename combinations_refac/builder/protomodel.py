#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, tempfile, os, time, colorama, subprocess, copy
from builder.protoxsecs import ProtoModelXSecs
from tester.combiner import Combiner
from tools import helpers


class ProtoModel:
    """ encodes one theoretical model, i.e. the particles, their masses, their
        branchings, their signal strength modifiers.
    """
    LSP = 1000022 ## the LSP is hard coded

    def __init__ ( self, walkerid, keep_meta = True, nevents = 10000 ):
        """
        :param keep_meta: If True, keep also all the data in best combo (makes
                          this a heavyweight object)
        :param nevents: minimum number of MC events when computing cross-sections
        """
        self.walkerid = walkerid
        self.keep_meta = keep_meta ## keep all meta info? big!
        self.version = 1 ## version of this class
        self.maxMass = 2400. ## maximum masses we consider
        self.minevents = nevents #Minimum number of events for computing xsecs
        self.nevents = nevents #Initial number of events for computing xsecs
        self.step = 0 ## count the steps
        self.particles = [ 1000001, 2000001, 1000002, 2000002, 1000003, 2000003,
                  1000004, 2000004, 1000005, 2000005, 1000006, 2000006, 1000011,
                  2000011, 1000012, 1000013, 2000013, 1000014, 1000015, 2000015,
                  1000016, 1000021, 1000022, 1000023, 1000025, 1000035, 1000024,
                  1000037 ]
        self.onesquark = False ## only one light squark
        self.twosquark = False  ## a few squarks, but not all
        self.manysquark = True ## many squarks
        if self.onesquark:
            self.particles = [ 1000001, 1000005, 1000006, 1000011, 1000012,
                      1000013, 1000014, 1000015,  1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "templates/template_1q.slha"
        if self.twosquark:
            self.particles = [ 1000001, 1000002, 1000004, 1000005, 1000006, 1000011,
                      1000012, 1000013, 1000014, 1000015, 1000016, 1000021, 1000022,
                      1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "templates/template_2q.slha"
        if self.manysquark:
            self.particles = [ 1000001, 1000002, 1000003, 1000004, 1000005, 1000006,
                      2000005, 2000006, 1000011, 1000012, 1000013, 1000014, 1000015,
                      1000016, 1000021, 1000022, 1000023, 1000025, 1000024, 1000037 ]
            self.templateSLHA = "templates/template1g.slha"
            if False:
                self.particles.append ( 2000021 )
                self.particles.append ( 3000006 )
                self.templateSLHA = "templates/template2g.slha"
            # self.templateSLHA = "templates/template_many.slha"
        self.templateSLHA = os.path.join ( os.path.dirname ( __file__ ), self.templateSLHA )
        self.possibledecays = {} ## list all possible decay channels
        self.decays = {} ## the actual branchings
        self.masses = {}
        self._stored_xsecs = () #Store cross-sections. It should only be accesses through getXsecs()!
        self._xsecMasses = {} #Store the masses used for computing the cross-sections
        self._xsecSSMs = {} #Store the signal strenght multiplier used for computing the cross-sections
        self.ssmultipliers = {} ## signal strength multipliers
        self.rvalues = [] ## store the r values of the exclusion attempt
        self.tpList = [] ## store information about the theory predictions
        self.llhd=0.
        self.muhat = 1.
        self.Z = 0.0
        self.K = None
        self.rmax = 0.
        self.letters = ""
        self.description = ""
        self.bestCombo = None

        with open ( self.templateSLHA ) as slhaf:
            tmp = slhaf.readlines()
            slhalines = []
            for line in tmp:
                p = line.find("#" )
                if p > -1:
                    line = line[:p]
                if "D" in line and not "DECAY" in line:
                    slhaline = line.strip().split(" ")[0]
                    # print ( "slhaline", slhaline )
                    slhalines.append ( slhaline )

        self.initializeSSMs( overwrite = True )
        for p in self.particles:
            self.masses[p]=1e6
            decays = []
            self.decays[p]={}
            for line in slhalines:
                if "D%s" % p in line:
                    p1 = line.find("_")+1
                    dpid = int ( line[p1:] )
                    dpid2 = None
                    if line.count("_")==2:
                        p2 = line.rfind("_")
                        dpid = int ( line[p1:p2] )
                        dpid2 = int(line[p2+1:])
                    dpd = dpid
                    if dpid2 != None:
                        dpd = (dpid,dpid2)
                    decays.append ( dpd )
                    self.decays[p][dpd]=0.
                    # print ( "p", p, "dpid", dpid, "dpid2", dpid2, "line", line )
                    if dpid == ProtoModel.LSP and sum(self.decays[p].values())<.5:
                        self.decays[p][dpd]=1.
            self.possibledecays[p]=decays

        ## the LSP we need from the beginning
        self.masses[ProtoModel.LSP]=random.uniform(200,500)

    def __str__(self):
        """ return basic information on model
        """

        pNames = [helpers.getParticleName ( pid ) for pid in self.unFrozenParticles()]
        pNames = ','.join(pNames)
        pStr = 'ProtoModel (%s): K = %1.2f, Z = %1.2f' %(pNames,self.K,self.Z)
        return pStr

    def __repr__(self):
        """ shorted version of __str__"""

        pStr = 'ProtoModel (%1.2f, %1.2f)' %(self.K,self.Z)
        return pStr

    def hasAntiParticle ( self, pid ):
        """ for a given pid, do i also have to consider its antiparticle
            -pid in the signal strength multipliers? """
        if pid in [ 1000021, 1000022, 1000023, 1000025, 1000035, 1000012,
                    1000014, 1000016, 2000012, 2000014, 2000016, 2000021 ]:
            return False
        return True

    def toTuple ( self, pid1, pid2 ):
        """ turn pid1, pid2 into a sorted tuple """
        a=[pid1,pid2]
        a.sort()
        return tuple(a)

    def getXsecs(self):
        """
        Return the cross-sections.
        If they have already been computed (and stored in self._stored_xsecs)
        AND the masses and signal strength multipliers habe not been modified, return the stored value.
        Otherwise, re-compute the cross-sections.

        :return: list of cross-sections
        """

        #If xsecMasses has not been defined or differs from current masses,
        #recompute xsecs
        if self.masses == self._xsecMasses and self.ssmultipliers == self._xsecSSMs:
            if self._stored_xsecs:
                return self._stored_xsecs

        #If something has changed, re-compute the cross-sections.
        #Xsecs are computed, self._xsecMasses and self._xsecSSM are updated.
        #The results are sored in the SLHA and self._stored_xsec.
        self.computeXSecs(nevents = self.nevents)

        return self._stored_xsecs

    def getOpenChannels(self,pid):
        """get the list of open decay channels for particle pid. Open channels are
        the decays to unfrozen particles and to lighter particles.

        :param pid: PID for particle

        :return: List with the daughter pids for each decay channel
        """

        #Get list of possible decay channels:
        openChannels = set()
        unfrozen = self.unFrozenParticles()
        for dpid in self.possibledecays[pid]:
            #Get the list of BSM particles in the decay:
            if isinstance(dpid,(list,tuple)):
                pidList = [abs(p) for p in dpid if p in self.masses]
            else:
                pidList = [abs(dpid)]
            #Skip decays to unfrozen particles
            if not all([dp in unfrozen for dp in pidList]):
                continue
            #Get total daughter mass (it should only be a single mass)
            mdaughter = sum([self.masses[p] for p in pidList])
            #Skip decays to heavier particles
            if mdaughter >= self.masses[pid]:
                continue
            openChannels.add ( dpid )

        openChannels = list(openChannels)

        return openChannels

    def setSSM ( self, pids, value=1., overwrite=True ):
        """ set the signal strength multiplier of pids to value.
            if overwrite = false, then do this onle if ssm is not defined """
        if overwrite:
            self.ssmultipliers [ pids ] = value
            return
        if not pids in self.ssmultipliers:
            self.ssmultipliers[pids] = value

    def initializeSSMs ( self, overwrite ):
        """ initialize signal strength multipliers, set them all to unity
        :param overwrite: if true, always set to one. if false, then initialize
                          only if not yet defined.
        """
        for p in self.particles:
            for q in self.particles:
                self.setSSM ( self.toTuple(p,q), 1., overwrite )
                if self.hasAntiParticle ( q ):
                    self.setSSM ( self.toTuple(p,-q), 1., overwrite )
            if self.hasAntiParticle ( p ):
                for q in self.particles:
                    self.setSSM ( self.toTuple(-p,q), 1., overwrite )
                    if self.hasAntiParticle ( q ):
                        self.setSSM ( self.toTuple ( -p, -q ), 1., overwrite )

    def highlight ( self, msgType = "info", *args ):
        """ logging, hilit """
        col = colorama.Fore.GREEN
        if msgType.lower() in [ "error", "red" ]:
            col = colorama.Fore.RED
        elif msgType.lower() in [ "warn", "warning", "yellow" ]:
            col = colorama.Fore.YELLOW
        elif msgType.lower() in [ "green", "info" ]:
            col = colorama.Fore.GREEN
        else:
            self.highlight ( "red", "i think we called highlight without msg type" )
        print ( "%s[model:%d - %s] %s%s" % ( col, self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)), colorama.Fore.RESET ) )
        self.log ( *args )

    def pprint ( self, *args ):
        """ logging """
        print ( "[model:%d] %s" % (self.walkerid, " ".join(map(str,args))) )
        self.log ( *args )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[model:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def frozenParticles ( self ):
        """ returns a list of all particles that can be regarded as frozen
            (ie mass greater than 1e5 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)>1e5:
                ret.append(m)
        return ret

    def cleanBestCombo ( self ):
        """ remove unneeded stuff before storing """
        if hasattr ( self, "keep_meta" ) and self.keep_meta:
            return ## dont remove best combo
        combiner = Combiner( self.walkerid )
        if hasattr ( self, "bestCombo" ) and self.bestCombo != None:
            self.bestCombo = combiner.removeDataFromBestCombo ( self.bestCombo )

    def almostSameAs ( self, other ):
        """ check if a model is essentially the same as <other> """
        if len ( self.masses.keys() ) != len ( other.masses.keys() ):
            return False
        ## check the masses
        for pid,m in self.masses.items():
            om = other.masses[pid]
            if m == 0.:
                if om == 0.:
                    continue
                else:
                    return False
            if abs ( om - m ) / m > 1e-5:
                return False
        ## now check ssmultipliers
        pidpairs = set ( self.ssmultipliers.keys() )
        pidpairs = pidpairs.union ( set ( other.ssmultipliers.keys() ) )
        for pidpair in pidpairs:
            ss = 1.
            if pidpair in self.ssmultipliers.keys():
                ss = self.ssmultipliers[pidpair]
            os = 1.
            if pidpair in other.ssmultipliers.keys():
                os = other.ssmultipliers[pidpair]
            if ss == 0.:
                if os == 0.:
                    continue
                else:
                    return False
                if abs ( ss - os ) / ss > 1e-6:
                    return False
        ## now check decays
        pids = set ( self.decays.keys() )
        pids = pids.union ( set ( other.decays.keys() ) )
        for pid in pids:
            sdecays, odecays = {}, {}
            if pid in self.decays:
                sdecays = self.decays[pid]
            if pid in other.decays:
                odecays = other.decays[pid]
            dpids = set ( sdecays.keys() )
            dpid = dpids.union ( set ( odecays.keys() ) )
            for dpid in dpids:
                sbr, obr = 0., 0.
                if dpid in sdecays:
                    sbr = sdecays[dpid]
                if dpid in odecays:
                    obr = odecays[dpid]
                if sbr == 0.:
                    if obr < 1e-6:
                        continue
                    else:
                        return False
                if abs ( sbr - obr ) / sbr > 1e-6:
                    return False
        return True

    def unFrozenParticles ( self, withLSP=True ):
        """ returns a list of all particles that can be regarded as unfrozen
            (ie mass less than 5e3 GeV) """
        ret = []
        for m,v in self.masses.items():
            if abs(v)<5e3:
                ret.append(m)
        if not withLSP and self.LSP in ret:
            ret.remove(self.LSP)
        return ret

    def createNewSLHAFileName ( self, prefix = "cur" ):
        """ create a new SLHA file name. Needed when e.g. unpickling """
        self.currentSLHA = tempfile.mktemp( prefix=".%s%s_" % ( prefix, self.walkerid ),
                                            suffix=".slha",dir="./")

    def checkTemplateSLHA ( self ):
        if not os.path.exists ( self.templateSLHA ):
            if "/mnt/hephy/" in self.templateSLHA:
                trySLHA = self.templateSLHA.replace("/scratch-cbe/users/wolfgan.waltenberger/git/smodels-utils/combinations/","./" )
                if os.path.exists ( trySLHA ):
                    self.templateSLHA = trySLHA
                    return

    def printMasses( self ):
        """ convenience function to print masses with particle names """
        particles = []
        for pid,m in self.masses.items():
            if m > 99000:
                continue
            particles.append ( "%s: %d" % (  helpers.getParticleName ( pid ), m ) )
        print ( ", ".join ( particles ) )

    def createSLHAFile ( self, nevents = None ):
        """ from the template.slha file, create the slha file of the current
            model.
        :param nevents: If defined, cross-sections will be computed with this number of MC events,
                        if None, the value is chosen according to self.minevents and self.Z.
        """

        #If number of events has not been specified, use Z value to estimate the
        #required number and update self.nevents:
        if not nevents:
            if self.Z > 2.5:
                self.nevents = max(self.minevents,50000)
            elif self.Z > 2.7:
                self.nevents = max(self.minevents,100000)
        else:
            self.nevents = nevents

        self.log ( "now create slha file via with %d events" % self.nevents )
        self.checkTemplateSLHA()
        with open( self.templateSLHA ) as f:
            lines=f.readlines()
        if not hasattr ( self, "currentSLHA" ):
            self.createNewSLHAFileName()

        unfrozen = self.unFrozenParticles()
        outputSLHA = self.currentSLHA
        if os.path.exists ( outputSLHA ):
            cmd = "cp %s %s" % ( outputSLHA, outputSLHA.replace(".cur",".old" ) )
            subprocess.getoutput ( cmd )
        self.log ( "create %s from %s" % (outputSLHA, self.templateSLHA ) )
        with open(outputSLHA,"w") as f:
            for line in lines:
                for m,v in self.masses.items():
                    line=line.replace("M%d" % m,"%.1f" % v )
                    if not m in self.decays:
                        if m != self.LSP and m in unfrozen:
                            self.highlight ( "red", "could not find %s in decays. keys are %s." % ( m, list(self.decays.keys()) ) )
                        #Assign dummy BR if None found
                        self.decays[m]={ self.LSP: 1.0 }

                    for dpid,dbr in self.decays[m].items():
                        if type(dpid)==tuple:
                            line=line.replace("D%d_%d_%d" % ( m, dpid[0],dpid[1]), "%.5f" % dbr )
                        else:
                        # print ( "dpid", dpid )
                            line=line.replace("D%d_%d" % ( m, dpid), "%.5f" % dbr )
                    D_ = "D%d_" % m
                    if D_ in line and not line[0]=="#":
                        p1= line.find(D_)
                        p2 = line[p1+1:].find(" ")
                        if not "D" in line[p1:p1+p2+1]:
                            self.pprint ( "remaining token %s set to zero." % \
                                    line[p1:p1+p2+1] )
                        line=line.replace( line[p1:p1+p2+1], "0." )
                f.write ( line )

        #Compute the cross-sections (if necessary) and store them to the file:
        self.getXsecs()

        return outputSLHA

    def dict ( self ):
        """ return the dictionary that can be written out """
        return { "masses": self.masses, "ssmultipliers": self.ssmultipliers,
                 "decays": self.decays }

    def relevantSSMultipliers ( self ):
        """ of all the ss mulipliers, return only the relevant ones,
            i.e. the ones for unfrozen particles and value != 1 """
        ret = {}
        frozen = self.frozenParticles()
        for pids,v in self.ssmultipliers.items():
            if abs ( v - 1. ) < 1e-5:
                continue
            isRelevant = True
            for pid in pids:
                if abs(pid) in frozen:
                    isRelevant = False
            if isRelevant:
                ret[pids]=v
        return ret

    def describe ( self ):
        """ describe a bit the protomodel """
        ndecays,nd = 0, 0
        for k,v in p.decays.items():
            if k == ProtoModel.LSP: ## dont count LSP
                continue
            ndecays += len(v)
            nd += 1
        nssms = len(p.ssmultipliers)
        print ( "%d masses, %d[%d] decays, %d ss multipliers" % \
                (len(p.masses), ndecays, nd, nssms ) )

    def delXSecs ( self ):
        """ delete stored cross section, if they exist """
        self._stored_xsecs = ()
        self._xsecMasses = {}
        self._xsecSSMs = {}

    def computeXSecs ( self, nevents = None ):
        """ compute xsecs for current.slha. The results are stored in the SLHA file and self._stored_xsecs.
        :param nevents: If defined, cross-sections will be computed with this number of MC events,
                        if None, the value used is self.nevents.

        """

        if not nevents:
            nevents = self.nevents
        if not hasattr ( self, "currentSLHA" ) or not os.path.exists ( self.currentSLHA ):
            self.pprint ( "compute xsecs called, but no slha file exists. I assume you meant to call createSLHAFile instead." )
            self.createSLHAFile(nevents = nevents )
            return

        computer = ProtoModelXSecs( self.walkerid, nevents, self.currentSLHA,
                                     self.relevantSSMultipliers(), self.step )
        try:
            computer.checkIfReadable()
        except Exception:
            pass
        try:
            xsecs,comment = computer.compute()
            self._stored_xsecs = ( xsecs, comment )
            self._xsecMasses = dict([[pid,m] for pid,m in self.masses.items()])
            self._xsecSSMs = dict([[pid,ssm] for pid,ssm in self.ssmultipliers.items()])
        except Exception:
            pass

    def copy(self, cp_predictions = False):
        """
        Create a copy of self. If cp_predictions the bestCombo and tpList attributes
        is copied using deepcopy.

        :returns: copy of protomodel
        """

        #Initialize empty model:
        newmodel = self.__class__( self.walkerid )

        #Copy information
        newmodel.keep_meta = self.keep_meta
        newmodel.maxMass = self.maxMass
        newmodel.minevents = self.minevents
        newmodel.nevents = self.nevents
        newmodel.step = self.step
        newmodel.particles = self.particles[:]
        newmodel.onesquark = self.onesquark ## only one light squark
        newmodel.twosquark = self.twosquark  ## a few squarks, but not all
        newmodel.manysquark = self.manysquark ## many squarks
        newmodel.templateSLHA = self.templateSLHA[:]
        newmodel.possibledecays = dict([[key,val] for key,val in self.possibledecays.items()])
        decayDict = {}
        for pid,dec in self.decays.items():
            decayDict[pid] = dict([[dpids,br] for dpids,br in dec.items()])
        newmodel.decays = decayDict
        newmodel.masses = dict([[pid,mass] for pid,mass in self.masses.items()])
        newmodel.ssmultipliers = dict([[pidPair,mass] for pidPair,mass in self.ssmultipliers.items()])
        newmodel.rvalues = self.rvalues[:]
        newmodel.llhd = self.llhd
        newmodel.muhat = self.muhat
        newmodel.Z = self.Z
        newmodel.rmax = self.rmax
        newmodel.letters = self.letters[:]
        newmodel.description = self.description[:]
        newmodel._stored_xsecs = copy.deepcopy(self._stored_xsecs)
        newmodel._xsecSSMs = dict([[pid,ssm] for pid,ssm in self._xsecSSMs.items()])
        newmodel._xsecMasses = dict([[pid,m] for pid,m in self._xsecMasses.items()])
        if cp_predictions:
            newmodel.tpList = copy.deepcopy(self.tpList)
            newmodel.bestCombo = copy.deepcopy(self.bestCombo)

        return newmodel

if __name__ == "__main__":
    p = ProtoModel( 1 )
    p.createSLHAFile()
    p.computeXSecs()

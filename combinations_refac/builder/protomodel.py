#!/usr/bin/env python3

""" Class that encapsulates a BSM model. """

import random, tempfile, os, time, colorama, subprocess
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
        self.ssmultipliers = {} ## signal strength multipliers
        self.rvalues = [] ## store the r values of the exclusion attempt
        self.tpList = [] ## store information about the theory predictions
        self.llhd=0.
        self.muhat = 1.
        self.Z = 0.
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

    def oldZ( self ):
        if not hasattr ( self, "_backup" ):
            self.pprint ( "asked for old Z, but no backup available" )
            return -.1
        return self._backup["Z"]

    def oldK( self ):
        if not hasattr ( self, "_backup" ):
            self.pprint ( "asked for old K, but no backup available" )
            return -20.
        if not "K" in self._backup:
            return -20.
        return self._backup["K"]

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

    def createSLHAFile ( self, outputSLHA=None, recycle_xsecs = False, nevents = None ):
        """ from the template.slha file, create the slha file of the current
            model.
        :param outputSLHA: if not None, write into that file. else, write into
            currentSLHA file.
        :param recycle_xsecs: if False, compute xsecs from scratch,
                              if True, recycle them, if possible.
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
        if outputSLHA == None:
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
                        if m != self.LSP:
                            self.highlight ( "red", "could not find %s in decays. keys are %s." % ( m, list(self.decays.keys()) ) )
                        ## FIXME what is this???
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
        self.computeXSecs( recycle = recycle_xsecs, nevents = self.nevents )
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
        if not hasattr ( self, "stored_xsecs" ):
            return
        del self.stored_xsecs

    def computeXSecs ( self, recycle=False, nevents = None ):
        """ compute xsecs for current.slha
        :param recycle: if False, dont store xsecs, always recompute.
                        if True, recycle the xsecs if they exist, store them.
        :param nevents: If defined, cross-sections will be computed with this number of MC events,
                        if None, the value used is self.nevents.

        """

        if not nevents:
            nevents = self.nevents
        if not hasattr ( self, "currentSLHA" ) or not os.path.exists ( self.currentSLHA ):
            self.pprint ( "compute xsecs called, but no slha file exists. I assume you meant to call createSLHAFile instead." )
            self.createSLHAFile(recycle_xsecs = recycle )
            return

        computer = ProtoModelXSecs( self.walkerid, nevents, self.currentSLHA,
                                     self.relevantSSMultipliers(), self.step )
        if recycle and hasattr ( self, "stored_xsecs" ):
            self.log ( "found %d old xsecs, will recycle them!!" % \
                       len(self.stored_xsecs[0]) )
            computer.addInfoToFile ( self.stored_xsecs )
            return
        if recycle:
            self.pprint ( "recycling is on, but no xsecs were found. compute with %d events." % nevents )
        try:
            computer.checkIfReadable()
        except Exception:
            pass
        try:
            xsecs,comment = computer.compute()
            if recycle: ## store them
                self.stored_xsecs = ( xsecs, comment )
        except Exception:
            pass

if __name__ == "__main__":
    p = ProtoModel( 1 )
    p.createSLHAFile()
    p.computeXSecs()

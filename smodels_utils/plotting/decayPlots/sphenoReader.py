"""
.. module: sphenoReader
        :synopsis: Module for reading and parsing the input slha files.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function

from pyparsing import Word, nums, ParseException, Optional, alphanums 
import pyslha
import logging
logger = logging.getLogger(__name__)

class SPhenoReader:
    """ a class that parses a spheno file """

    def setIds( self ):
        """ Define the ids and the names"""
        self.ids={
          1: "u", 2: "d", 3: "s", 4: "c",
          5: "b", 6: "t", 
          11: "e", 13: "mu", 15: "tau",
          12: "nu", 14: "nu", 16:"nu",
          21: "g", 22: "gamma", 24: "W", 23:"Z", 25:"h", 35: "H", 36: "a0",
          37: "h+", 
          1000001: "~d_L", 2000001: "~d_R",
          1000002: "~u_L", 2000002: "~u_R",
          1000003: "~s_L", 2000003: "~s_R",
          1000004: "~c_L", 2000004: "~c_R",
          1000005: "~b_1", 2000005: "~b_2",
          1000006: "~t_1", 2000006: "~t_2",
          1000011: "~e_L", 1000012: "~nu_e",
          1000013: "~mu_L", 1000014: "~nu_mu",
          1000015: "~tau_L", 1000016: "~nu_tau",
          2000011: "~e_R", 2000012: "~nu_eR",
          2000013: "~mu_R", 2000014: "~nu_muR",
          2000015: "~tau_R", 2000016: "~nu_tauR",
          1000021: "~g", 1000022: "~chi10",
          1000024: "~chi1+", 1000023: "~chi20",
          1000037: "~chi2+", 1000025: "~chi30",
          1000035: "~chi40"
        }
        tmp = {}
        for (key,value) in self.ids.items():
          tmp[value]=key
        for k,v in tmp.items():
            self.ids[k]=v

    def parseNamesAndMasses( self ):
        try:
          self.setIds()
          masses=self.pyslha.blocks["MASS"] ## pyslha[1]
          tmp = {}
          for pdgid,value in masses.items():
            self.masses[pdgid]=float(value)
        except Exception as e:
            logger.error ( f"Exception in ``parseNamesAndMasses'': {e}" )

    def fullName ( self, pdgid, integrated=False ):
        """ get the full name of pdgid """
        if type(pdgid)==type(1) and pdgid in self.ids.keys ( ):
          return self.ids[pdgid]
        return str(pdgid)

    def name ( self, pdgid, integrated=False ):
        """ get the name of the particle, given pdgid """
        if self.separatecharm and abs(pdgid)==4:
          return "c"
        if integrated and abs(pdgid)<4:
          return "q"
        if self.integrateLeptons and type(pdgid)==type(1) and abs(pdgid)==11:
          return "l"
        if type(pdgid)==type(1) and pdgid in self.ids.keys ( ):
          return self.ids[pdgid]
        return str(pdgid)

    def getRelevantParticles ( self, start, rmin=0.1 ):
        """ get the relevant particles chasing down <start> """
        import copy
        ret2={}
        ret2id={}
        for m in start:
            if len(self.getDecays(m,rmin))>0:
                ret2[m]=1
            if not m in self.decays.keys ( ):
                continue
            for (daughter,right) in self.decays[m].items():
              for (radiator,r) in right.items():
                if r>rmin:
                    ret2[daughter]=1
                    ret2id[daughter]=1
        for nsteps in range(2):
            ret3id=copy.deepcopy(ret2id)
            for i in ret2id:
                if not i in self.decays.keys ():
                    continue
                for (daughter,right) in self.decays[i].items():
                    for (radiator,r) in right.items():
                        if r>rmin:
                            ret2[daughter]=1
                            ret3id[daughter]=1
            ret2id=copy.deepcopy(ret3id)
        names = list( ret2.keys() )
        return names

    def printMassTable ( self ):
        print ( "SPhenoReader Mass Table" )
        print ( "-----------------------" )
        for (k,v) in self.masses.items():
          print ( f"{self.name(k):>10}: {int(v)} GeV" )

    def getMass ( self, name ):
        pdgid=self.pdgId ( name )
        if pdgid in self.masses.keys ( ):
          return self.masses[pdgid]
        return 0.

    def hasTeVScaleMass ( self, name ):
        """ does <name> have a mass and is it < 10 TeV? 
        :param name: can be a name or a pid
        """
        pdgid=self.pdgId ( name )
        if pdgid in self.masses.keys ( ):
            m = self.masses[pdgid]
            if m < 10000. and m > 0.:
                return True
            else:
                return False
        return False

    def spin ( self, pid ):
        """ get the spin of pid, assuming SUSY """
        if pid in [ 1000022, 1000023, 1000024, 1000021, 1000025, 1000035, 1000037 ]:
            return 0.5
        return 0
        """
        if name=="~g" or name[:4]=="~chi":
          return 0.5
        if name[:3] in [ "~u_", "~d_", "~l_", "~b_", "~s_", "~c_", "~t_", "~q_", "~e_" ]:
          return 0
        if name[:3] in [ "~nu", "~mu", "~ta" ]:
          return 0
        return 0
        """

    def fermionic ( self, pid ):
        """ is pid fermionic (in SUSY notation) """
        if pid in [ 1000022, 1000023, 1000024, 1000021, 1000025, 1000035, 1000037 ]:
            return True
        return False
        """
        if name=="~g" or name[:4]=="~chi":
          return True
        return False
        """

    def bosonic ( self, name ):
        return not self.fermionic ( name )

    def merge ( self, p1, p2 ):
        """ merge pdg p1 with pdg p2, only for the squarks """
        m1=self.masses[p1]
        m2=self.masses[p2]
        n1=self.ids[p1]
        n2=self.ids[p2]
        if math.fabs ( m2 - m1 ) > 25:
          logger.error ( f"cannot merge {n1} with {n2}" )
          return
        self.masses[p1]=(m1+m2)/2.
        self.masses.pop(p2)
        self.ids.pop(p2)
        self.ids.pop(n2)
        n3=f"{n1},{n2[-1:]}"
        self.ids[p1]=n3

    def getMasses ( self ):
        ret={}
        for (k,v) in self.masses.items():
          ret[self.name(k)]=v
        return ret

    def printDecay ( self, mother, rmin=0.0 ):
        m=self.pdgId ( mother )
        if not m in self.decays.keys ( ):
          logger.error ( f"no decays for {self.name (m )}" )
          return
        rtotal=0.
        for (daughter,right) in self.decays[m].items():
          for ( radiator, r ) in right.items():
            if r>rmin:
              logger.debug ( "%8s -> %8s %8s: %.2f" % \
                ( self.name(m), str(daughter), radiator, r ) )
            rtotal+=r

    def printDecays ( self ):
        print ( "SPhenoReader Decay Table" )
        print ( "--------------------------" )
        for mother in self.decays:
          self.printDecay ( mother )


    def checkDecayTable ( self ):
        """ check if the mother branchings add up to about 1.0 """
        for (mother,decs) in self.decays.items():
          rtotal=0.
          for (daughter,right) in decs.items():
            for ( radiator, r ) in right.items():
              #if type(r)==type("a"):
              #  """ simplified models, no need to check """
              #  return
              rtotal+=r
          absdiff = abs ( rtotal - 1.0 )
          if absdiff > 0.03:
            mname = self.name ( mother )
            mmass = self.masses[mother]
            if mmass < 90000.:
                logger.error ( f"[sphenoReader:warning] {mname} branchings add up to {rtotal:.2f}, mass of {mname} is {self.masses[mother]} " )
            return
          if absdiff > 0.01:
            logger.warn ( f"[sphenoReader:warning] {self.name(mother)} branchings add up to {rtotal:.2f}" )
            return

    def integratePdgs ( self, pdgid ):
        """ for branching ratios, we dont want to differentiate
            between e.g. u and d, so we have a pdg map """
        apdg=abs(pdgid)
        if apdg==4 and self.separatecharm: return 4
        if apdg<5:
          apdg=1
        if self.integrateLeptons:
          if apdg==11 or apdg==13 or apdg==15:
            apdg=11
        return apdg

    def parseBranchings ( self ):
        """ get the branching ratios """
        try:
          f=open(self.filename)
          inDecay=False
          pdgIdMother=0
          for lline in f:
            lline=lline.replace("\n","")
            if len(lline)==0:
              continue
            if lline[0]=='#':
             continue
            line=lline.lower()
            if line.find("xsection")==0:
              continue
            if line.find("decay")==0:
              inDecay=True
              tokens=line.split()
              pdgIdMother=int(tokens[1])
              continue
            if line.find("block")==0:
              inDecay=False
            if not inDecay:
              continue
            if line.find("#    br")==0:
              # title line
              continue
            if not pdgIdMother in self.decays.keys ( ):
              self.decays[pdgIdMother]={}
              self.fulldecays[pdgIdMother]={}
            nbody=Word ( f"{nums}eE+-." )+Word ( f"{nums}-" )+ Word ( f"{nums}-" ) +\
                  Word ( f"{nums}-" ) + Optional ( Word ( f"{nums}-" ) )
            try:
              parsed=nbody.parseString ( line )
              r=float(parsed[0])
              ps= [ abs(int(parsed[2])),abs(int(parsed[3])) ]
              if len(parsed)>4:
                ps.append ( abs ( int( parsed[4]) ) )
              ps.sort()
              ps.reverse()
              radiate=self.name(self.integratePdgs(ps[1]),integrated=True)
              fradiate=self.fullName(self.integratePdgs(ps[1]),integrated=True)
              if len(parsed)>4:
                radiate+=f" {self.name(self.integratePdgs(ps[2]), integrated=True)}"
                fradiate+=f" {self.fullName(self.integratePdgs(ps[2]), integrated=True)}"
              if self.verbose:
                if len(parsed)<=4:
                  logger.debug ( f"{int(pdgIdMother)} -> {int(ps[0])}  {int(ps[1])}   ({r})" )
                else:
                  logger.debug ( f"{int(pdgIdMother)} -> {int(ps[0])}  {int(ps[1])}  {int(ps[2])}  ({r}) radiate={radiate} fradiate={fradiate}" )
              if not ps[0] in self.decays[pdgIdMother].keys ( ):
                self.decays[pdgIdMother][ps[0]]={}
                self.fulldecays[pdgIdMother][ps[0]]={}
              if not radiate in self.decays[pdgIdMother][ps[0]].keys ( ):
                if type(r)==float:
                  self.decays[pdgIdMother][ps[0]][radiate]=0.
                  self.fulldecays[pdgIdMother][ps[0]][fradiate]=0.
              self.decays[pdgIdMother][ps[0]][radiate]+=r
              self.fulldecays[pdgIdMother][ps[0]][fradiate]+=r
            except ParseException as e:
              logger.error ( "error, failed while trying to interpret "\
                    "the following line as a decay line" )
              logger.debug ( f"line >>{line}<<" )
          self.checkDecayTable()
        except Exception as e:
          logger.error ( f"exception in ``parseBranchings'': {e}" )

    def pdgId ( self, name ):
        if type(name)==type(3):
          return name
        if name in self.ids.keys ( ):
          return self.ids[name]
        return 0

    def exists ( self, name ):
        """ is this name listed? """
        if type(name)==type("a"):
            return name in self.ids.keys()

    def filterNames ( self, lst ):
        """ taking list <lst>, this returns a list of all names
            in <lst> that do exist """
        ret=[]
        for i in lst:
            if i in self.ids.keys ( ):
                ret.append ( i )
        return ret

    def getAllDecays ( self, particle ):
        """ get all decays, we're e.g. talking simplified models here """
        p=self.pdgId ( particle )
        ret={}
        if not p in self.decays.keys ():
            return ret
        for (daughter,right) in self.decays[p].items():
          dname=self.name ( daughter )
          for (radiator,r) in right.items():
            if not dname in ret.keys ( ):
              ret[dname]={}
            ret[dname][radiator]=r
        return ret

    def leptonicSignature ( self, particle ):
        """ particles which give rise to a leptonic signature return true here """
        if particle=="l" or particle=="t" or particle=="W" or \
           particle=="Z" or particle=="e" or particle=="mu":
          return True
        return False

    def hasLeptonicSignature ( self, particle, fraction=False ):
        """ if any particle in the string <particle> has leptonic signature,
            return true """
        logger.error ( "Lacks implementation" )
        if not fraction:
          ret=False
          while particle.find(" ")!=-1:
            pos=particle.find(" ")
            p=particle[:pos]
            particle=particle[pos:]
            logger.debug ( f"p=->{p}<- pp=->{particle}<=" )
          return ret
        return 0.0

    def getDecays ( self, pid, rmin=0.5, full=False ):
        """ get the leading decays, until rmin percentage of the branching ratio
            is covered 
        :param full: use self.fulldecays, not self.decays ?
        """
        ret={}
        # p=self.pdgId ( particle )
        if not pid in self.decays.keys ():
          return ret

        sorted_decays={}
        items=self.decays[pid].items()
        if full:
          items=self.fulldecays[pid].items()
        for (daughter,right) in items:
          for (radiator,r) in right.items():
            #if type(r)==type("a"):
            #  """ simplified models? return all decays! """
            #  return self.getAllDecays ( particle )
            if r<.01:
              continue
            t=int(r*10000)
            while t in sorted_decays.keys ():
              t+=1
            sorted_decays[t]=daughter
        s=sorted(sorted_decays)
        s.reverse()

        ret_r=0.0
        has_counted={}
        for t in s:
          daughter=sorted_decays[t]
          if not daughter in has_counted.keys():
            has_counted[daughter]={}
          right=self.decays[pid][daughter]
          if full:
            right=self.fulldecays[p][daughter]
          if str(right) in has_counted[daughter].keys ():
            continue
          has_counted[daughter][str(right)]=True
          for (radiator,r) in right.items():
            if r>rmin:
              if not daughter in ret.keys ( ):
                ret[daughter]={}
              ret[daughter][radiator]=r
              ret_r+=r
        return ret

    def __init__ ( self, filename, integrateLeptons=True, \
        integrateSquarks=True, verbose=False, separatecharm=False ):
      self.filename=filename
      self.pyslha=pyslha.readSLHAFile ( filename )
      self.masses={}
      self.ids={}
      self.integrateLeptons=integrateLeptons
      self.integrateSquarks=integrateSquarks
      self.separatecharm=separatecharm
      self.verbose=verbose
      self.parseNamesAndMasses()
      self.decays={}
      self.fulldecays={}
      self.parseBranchings()

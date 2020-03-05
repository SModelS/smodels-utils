#!/usr/bin/env python3

"""
.. module:: mg5Wrapper
        :synopsis: code that wraps around MadGraph5. Produces the data cards,
                   and runs the mg5 executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil, tempfile, time, socket
import multiprocessing
import bakeryHelpers

class MG5Wrapper:
    def __init__ ( self, nevents, topo, njets, keep, rerun, ma5, ver="2_6_5" ):
        """
        :param ver: version of mg5
        """
        self.topo = topo
        self.keep = keep
        self.rerun = rerun
        self.ma5 = ma5
        self.njets = njets
        self.mg5install = "./mg5"
        self.logfile = None
        self.logfile2 = None
        self.tempf = None
        self.ver = ver
        if not os.path.isdir ( self.mg5install ):
            self.error ( "mg5 install is missing??" )
        self.executable = self.mg5install + "/bin/mg5_aMC"
        if not os.path.exists ( self.executable ):
            self.info ( "cannot find mg5 installation at %s" % self.mg5install )
            self.exe ( "mg5/make.py" )
        self.templateDir = "templates/"
        self.mgParams = { 'EBEAM': '6500', # Single Beam Energy expressed in GeV
                          'NEVENTS': str(nevents), 'MAXJETFLAVOR': '5',
                          'PDFLABEL': 'cteq6l1', 'XQCUT': '50' } #, 'qcut': '90' }
        self.info ( "initialised" )

    def info ( self, *msg ):
        print ( "%s[mg5Wrapper] %s%s" % ( colorama.Fore.YELLOW, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def debug( self, *msg ):
        pass

    def msg ( self, *msg):
        print ( "[mg5Wrapper] %s" % " ".join ( msg ) )

    def error ( self, *msg ):
        print ( "%s[mg5Wrapper] %s%s" % ( colorama.Fore.RED, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def writePythiaCard ( self, process="" ):
        """ this method writes the pythia card for within mg5.
        :param process: fixme (eg T2_1jet)
        """
        self.runcard = tempfile.mktemp ( prefix="run", suffix=".card", dir="./" )
        # filename = "%s/Cards/run_card.dat" % process
        self.debug ( "writing pythia run card %s" % self.runcard )
        templatefile = self.templateDir+'/template_run_card.dat'
        if not os.path.exists ( templatefile ):
            self.error ( "cannot find %s" % templatefile )
            sys.exit()
        tfile = open( templatefile,'r')
        lines = tfile.readlines()
        tfile.close()
        g = open ( self.runcard, "w" )
        for line in lines:
            for k,v in self.mgParams.items():
                if k in line:
                    line = line.replace("@@%s@@" % k,v)
            g.write ( line )
        g.close()
        self.info ( "wrote run card %s" % self.runcard )

    def writeCommandFile ( self, process = "", masses = None ):
        """ this method writes the commands file for mg5.
        :param process: fixme (eg T2tt_1jet)
        """
        self.commandfile = tempfile.mktemp ( prefix="mg5cmd", dir="./" )
        f = open(self.commandfile,'w')
        f.write('set automatic_html_opening False\n' )
        f.write('launch %s\n' % bakeryHelpers.dirName(process,masses))
        f.write('shower=Pythia8\n')
        f.write('detector=OFF\n')
        #f.write('detector=Delphes\n')
        #f.write('pythia=ON\n')
        #f.write('madspin=OFF\n')
        f.write('0\n')
        f.write('0\n')
        f.close()

    def pluginMasses( self, slhaTemplate, masses ):
        """ take the template slha file and plug in
            masses """
        f=open(slhaTemplate,"r")
        lines=f.readlines()
        f.close()
        self.slhafile = tempfile.mktemp(suffix=".slha",dir="./" )
        f=open( self.slhafile,"w")
        n=len(masses)
        for line in lines:
            for i in range(n):
                line = line.replace ( "M%d" % (n-i-1), str(masses[i]) )
            f.write ( line )
        f.close()

    def run( self, masses, analyses, pid=None ):
        """ Run MG5 for topo, with njets additional ISR jets, giving
        also the masses as a list.
        """
        self.process = "%s_%djet" % ( self.topo, self.njets )
        if self.hasHEPMC ( masses ):
            if not self.rerun:
                self.info ( "hepmc file for %s exists. go directly to MA5." % \
                            str(masses) )
                self.runMA5 ( masses, analyses )
                return
            else:
                self.info ( "hepmc file for %s exists, but rerun requested." % str(masses) )
        self.info ( "running on %s in job #%s" % (masses, pid ) )
        slhaTemplate = "slha/%s_template.slha" % self.topo
        self.pluginMasses( slhaTemplate, masses )
        # first write pythia card
        self.writePythiaCard ( process=self.process )
        # then write command file
        self.writeCommandFile( process=self.process, masses=masses )
        # then run madgraph5
        self.execute ( self.slhafile, masses )
        self.unlink ( self.slhafile )
        self.runMA5 ( masses, analyses )

    def runMA5 ( self, masses, analyses ):
        """ run ma5, if desired """
        if not self.ma5:
            return
        from ma5Wrapper import MA5Wrapper
        ma5 = MA5Wrapper ( self.topo, self.njets, self.rerun, analyses )
        self.debug ( "now call ma5Wrapper" )
        ma5.run ( masses )

    def unlink ( self, f ):
        """ remove a file, if keep is not true """
        if self.keep:
            return
        if f == None:
            return
        if os.path.exists ( f ):
            subprocess.getoutput ( "rm -rf %s" % f )

    def exe ( self, cmd ):
        self.msg ( "now execute: %s" % cmd[:70] )
        ret = subprocess.getoutput ( cmd )
        if len(ret)==0:
            return
        maxLength=60
        # maxLength=560
        if len(ret)<maxLength:
            self.msg ( " `- %s" % ret )
            return
        self.msg ( " `- %s" % ( ret[-maxLength:] ) )

    def addJet ( self, lines, njets, f ):
        """ if 'generate' or 'add process' line, then append n jets to file f """
        for line in lines:
            if "generate" in line or "add process" in line:
                line = line.strip()
                line = line.replace ( "generate ", "add process " )
                if "$" in line and not " $" in line:
                   self.error ( "found a line with dollar and no space %s" % line )
                   self.error ( "please add a space before the dollar" )
                   sys.exit()
                if " $" in line:
                    line = line.replace(" $"," j"*njets+" $" )
                else:
                    line = line + " j"*njets
                line = line + "\n"
                f.write ( line )

    def execute ( self, slhaFile, masses ):
        templatefile = self.templateDir + '/MG5_Process_Cards/'+self.topo+'.txt'
        if not os.path.isfile( templatefile ):
            self.error ( "The process card %s does not exist." % templatefile )
            sys.exit()
        f=open(templatefile,"r")
        lines=f.readlines()
        f.close()
        self.tempf = tempfile.mktemp(prefix="mg5proc",dir="./")
        f=open(self.tempf,"w")
        f.write ( "import model_v4 mssm\n" )
        for line in lines:
            f.write ( line )
        for i in [ 1, 2, 3 ]:
            if self.njets >= i:
                self.addJet ( lines, i, f )

        Dir = bakeryHelpers.dirName ( self.process, masses )
        f.write ( "output %s\n" % Dir )
        f.close()
        if os.path.exists ( Dir ):
            subprocess.getoutput ( "rm -rf %s" % Dir )
        self.info ( "run mg5 for %s" % self.tempf )
        self.logfile = tempfile.mktemp ()
        cmd = "python2 %s %s 2>&1 | tee %s" % ( self.executable, self.tempf, self.logfile )
        self.exe ( cmd )
        ## copy slha file
        if not os.path.exists ( Dir+"/Cards" ):
            cmd = "rm -rf %s" % Dir 
            o = subprocess.getoutput ( cmd )
            self.error ( "%s/Cards does not exist! Skipping! %s" % ( Dir, o ) )
            self.exe ( cmd )
            return
        shutil.move(slhaFile, Dir+'/Cards/param_card.dat' )
        shutil.move(self.runcard, Dir+'/Cards/run_card.dat' )
        if (os.path.isdir(Dir+'/Events/run_01')):
            shutil.rmtree(Dir+'/Events/run_01')
        self.logfile2 = tempfile.mktemp ()
        cmd = "python2 %s %s 2>&1 | tee %s" % ( self.executable, self.commandfile, 
                                                self.logfile2 )
        self.exe ( cmd )
        self.clean()

    def clean ( self ):
        """ clean up temporary files """
        self.info ( "cleaning up %s, %s, %s, %s" % \
                ( self.commandfile, self.tempf, self.logfile, self.logfile2 ) )
        self.unlink ( self.commandfile )
        self.unlink ( self.tempf )
        self.unlink ( self.logfile )
        self.unlink ( self.logfile2 )

    def hasHEPMC ( self, masses ):
        """ does it have a valid HEPMC file? if yes, then skip the point """
        hepmcfile = bakeryHelpers.dirName(self.process,masses)+"/Events/run_01/tag_1_pythia8_events.hepmc.gz"
        if not os.path.exists ( hepmcfile ):
            return False
        if os.stat ( hepmcfile ).st_size < 100:
            ## too small to be real
            return False
        return True

def main():
    import argparse
    argparser = argparse.ArgumentParser(description='madgraph5 runner.')
    argparser.add_argument ( '-n', '--nevents', help='number of events to generate [10000]',
                             type=int, default=10000 )
    argparser.add_argument ( '-j', '--njets', help='number of ISR jets [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-p', '--nprocesses', help='number of process to run in parallel. 0 means 1 per CPU [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-t', '--topo', help='topology [T2]',
                             type=str, default="T2" )
    argparser.add_argument ( '-k', '--keep', help='keep temporary files',
                             action="store_true" )
    argparser.add_argument ( '--show', help='show production stats',
                             action="store_true" )
    argparser.add_argument ( '-a', '--ma5', help='run also ma5 after producing the events',
                             action="store_true" )
    argparser.add_argument ( '-c', '--clean', help='clean all temporary files, then quit',
                             action="store_true" )
    argparser.add_argument ( '-b', '--bake', help='call emCreator, bake .embaked files',
                             action="store_true" )
    argparser.add_argument ( '-C', '--clean_all', help='clean all temporary files, even Tx directories, then quit',
                             action="store_true" )
    argparser.add_argument ( '--copy', help='copy embaked file to smodels-database',
                             action="store_true" )
    argparser.add_argument ( '-l', '--list_analyses', help='print a list of MA5 analyses, then quit',
                             action="store_true" )
    anadef = "atlas_susy_2016_07"
    anadef = "cms_sus_16_033"
    argparser.add_argument ( '--analyses', help='analyses, comma separated [%s]' % anadef,
                             type=str, default=anadef )
    argparser.add_argument ( '--maxgap2', help='maximum mass gap between second and third, to force offshell [None]',
                             type=float, default=None )
    argparser.add_argument ( '-r', '--rerun', help='force rerun, even if there is a summary file already',
                             action="store_true" )
    #mdefault = "(2000,1000,10),(2000,1000,10)"
    mdefault = "(1000,2000,50),'half',(1000,2000,50)"
    argparser.add_argument ( '-m', '--masses', help='mass ranges, comma separated list of tuples. One tuple gives the range for one mass parameter, as (m_lowest, m_highest, delta_m). m_highest and delta_m may be omitted. Keyword "half" (add quotes) is accepted for intermediate masses. [%s]' % mdefault,
                             type=str, default=mdefault )
    args = argparser.parse_args()
    if args.list_analyses:
        bakeryHelpers.listAnalyses()
        sys.exit()
    if args.show:
        import printProdStats
        anas = args.analyses.split(",")
        for ana in anas:
            ana = bakeryHelpers.ma5AnaNameToSModelSName ( ana )
            printProdStats.main( ana )
        sys.exit()
    if args.clean:
        subprocess.getoutput ( "rm -rf mg5cmd* mg5proc* tmp*slha run*card" )
        print ( "Cleaned temporary files." )
        sys.exit()
    if args.clean_all:
        subprocess.getoutput ( "rm -rf mg5cmd* mg5proc* tmp*slha T*jet* run*card ma5/ANA_T* ma5_T* ma5.template/recast* ma5.template/ma5cmd*" )
        print ( "Cleaned temporary files." )
        sys.exit()
    hname = socket.gethostname()
    if hname.find(".")>0:
        hname=hname[:hname.find(".")]
    with open("baking.log","a") as f:
        cmd = ""
        for i,a in enumerate(sys.argv):
            if i>0 and sys.argv[i-1] in [ "-m", "--masses" ]:
                a='"%s"' % a
            if i>0 and sys.argv[i-1] in [ "--analyses" ]:
                a='"%s"' % a
            cmd += a + " "
        cmd = cmd[:-1]
        f.write ( "[%s] %s:\n%s\n" % ( hname, time.asctime(), cmd ) )
    nReqM = bakeryHelpers.nRequiredMasses ( args.topo )
    keepOrder=True
    if args.topo == "TGQ":
        keepOrder=False
    masses = bakeryHelpers.parseMasses ( args.masses, filterOrder=keepOrder, 
                                         maxgap2=args.maxgap2 )
    import random
    random.shuffle ( masses )
    nm = len(masses)
    if nReqM != len(masses[0]):
        print ( "Error: you gave %d masses, but %d are required for %s." % \
                ( len(masses[0]), nReqM, args.topo ) )
        sys.exit()
    nprocesses = bakeryHelpers.nJobs ( args.nprocesses, nm )
    mg5 = MG5Wrapper( args.nevents, args.topo, args.njets, args.keep, args.rerun, args.ma5 )
    # mg5.info( "%d points to produce, in %d processes" % (nm,nprocesses) )
    djobs = int(len(masses)/nprocesses)

    def runChunk ( chunk, pid ):
        for c in chunk:
            mg5.run ( c, args.analyses, pid )
        print ( "%s[runChunk] finished chunk #%d%s" % \
                ( colorama.Fore.GREEN, pid, colorama.Fore.RESET ) )

    jobs=[]
    for i in range(nprocesses):
        chunk = masses[djobs*i:djobs*(i+1)]
        if i == nprocesses-1:
            chunk = masses[djobs*i:]
        p = multiprocessing.Process(target=runChunk, args=(chunk,i))
        jobs.append ( p )
        p.start()
    if args.bake:
        import emCreator
        from types import SimpleNamespace
        # analyses = "atlas_susy_2016_07"
        analyses = args.analyses
        args = SimpleNamespace ( masses="all", topo=args.topo, njets=args.njets, \
                analyses = analyses, copy=args.copy, verbose=False )
        emCreator.run ( args )
    with open("baking.log","a") as f:
        cmd = ""
        for i,a in enumerate(sys.argv):
            if i>0 and sys.argv[i-1] in [ "-m", "--masses" ]:
                a='"%s"' % a
            cmd += a + " "
        cmd = cmd[:-1]
        # f.write ( "[%s] %s: ended: %s\n" % ( hname, time.asctime(), cmd ) )

if __name__ == "__main__":
    main()

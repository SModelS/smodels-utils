#!/usr/bin/env python3

"""
.. module:: mg5Wrapper
        :synopsis: code that wraps around MadGraph5. Produces the data cards,
                   and runs the mg5 executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil, tempfile
import multiprocessing
import bakeryHelpers

class MG5Wrapper:
    def __init__ ( self, nevents, topo, njets, keep, ver="2_6_5" ):
        """
        :param ver: version of mg5
        """
        self.topo = topo
        self.keep = keep
        self.njets = njets
        self.mg5install = "./mg5"
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
        sys.exit()

    def writePythiaCard ( self, process="" ):
        """ this method writes the pythia card for within mg5.
        :param process: fixme (eg T2_1jet)
        """
        filename = "run_card.dat"
        # filename = "%s/Cards/run_card.dat" % process
        self.debug ( "writing pythia run card %s" % filename )
        if os.path.exists ( filename ):
            os.unlink ( filename )
        templatefile = self.templateDir+'/template_run_card.dat'
        if not os.path.exists ( templatefile ):
            self.error ( "cannot find %s" % templatefile )
        tfile = open( templatefile,'r')
        lines = tfile.readlines()
        tfile.close()
        g = open ( filename, "w" )
        for line in lines:
            for k,v in self.mgParams.items():
                if k in line:
                    line = line.replace("@@%s@@" % k,v)
            g.write ( line )
        g.close()
        self.info ( "wrote run card %s" % filename )

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

    def run( self, masses, pid=None ):
        """ Run MG5 for topo, with njets additional ISR jets, giving
        also the masses as a list.
        """
        self.info ( "running on %s in job #%s" % (masses, pid ) )
        self.process = "%s_%djet" % ( self.topo, self.njets )
        slhaTemplate = "slha/%s_template.slha" % self.topo
        self.pluginMasses( slhaTemplate, masses )
        # first write pythia card
        self.writePythiaCard ( process=self.process )
        # then write command file
        self.writeCommandFile( process=self.process, masses=masses )
        # then run madgraph5
        self.execute ( self.slhafile, masses )
        self.unlink ( self.slhafile )

    def unlink ( self, f ):
        """ remove a file, if keep is not true """
        if self.keep:
            return
        if os.path.exists ( f ):
            subprocess.getoutput ( "rm -rf %s" % f )

    def exe ( self, cmd ):
        self.msg ( "now execute: %s" % cmd )
        ret = subprocess.getoutput ( cmd )
        if len(ret)==0:
            return
        # maxLength=60
        maxLength=560
        if len(ret)<maxLength:
            self.msg ( " `- %s" % ret )
            return
        self.msg ( " `- %s" % ( ret[-maxLength:] ) )
        # self.msg ( " `- %s ... %s" % ( ret[:maxLength/2-1], ret[-maxLength/2-1:] ) )

    def execute ( self, slhaFile, masses ):
        templatefile = self.templateDir + '/MG5_Process_Cards/'+self.topo+'.txt'
        if not os.path.isfile( templatefile ):
            self.error ( "The process card %s does not exist." % templatefile )
        f=open(templatefile,"r")
        lines=f.readlines()
        f.close()
        tempf = tempfile.mktemp(prefix="mg5proc",dir="./")
        f=open(tempf,"w")
        for line in lines:
            f.write ( line )
        if self.njets > 0:
            for line in lines:
                if "generate" in line:
                    line = line.replace ( "generate ", "add process " )
                    f.write ( line.strip() + " j\n" )
        if self.njets > 1:
            for line in lines:
                if "generate" in line:
                    line = line.replace ( "generate ", "add process " )
                    f.write ( line.strip() + " j j\n" )
        if self.njets > 2:
            for line in lines:
                if "generate" in line:
                    line = line.replace ( "generate ", "add process " )
                    f.write ( line.strip() + " j j j\n" )

        Dir = bakeryHelpers.dirName ( self.process, masses )
        f.write ( "output %s\n" % Dir )
        f.close()
        if os.path.exists ( Dir ):
            subprocess.getoutput ( "rm -rf %s" % Dir )
        self.info ( "run mg5 for %s" % tempf )
        cmd = "python2 %s %s" % ( self.executable, tempf )
        self.exe ( cmd )
        ## copy slha file
        shutil.copyfile(slhaFile, Dir+'/Cards/param_card.dat' )
        shutil.copyfile("run_card.dat", Dir+'/Cards/run_card.dat' )
        if (os.path.isdir(Dir+'/Events/run_01')):
            shutil.rmtree(Dir+'/Events/run_01')
        cmd = "python2 %s %s" % ( self.executable, self.commandfile )
        self.exe ( cmd )
        self.unlink ( self.commandfile )
        self.unlink ( tempf )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='madgraph5 runner.')
    argparser.add_argument ( '-n', '--nevents', help='number of events to generate [10]',
                             type=int, default=10 )
    argparser.add_argument ( '-j', '--njets', help='number of ISR jets [0]',
                             type=int, default=0 )
    argparser.add_argument ( '-p', '--nprocesses', help='number of process to run in parallel. 0 means 1 per CPU [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-t', '--topo', help='topology [T2]',
                             type=str, default="T2" )
    argparser.add_argument ( '-k', '--keep', help='keep temporary files',
                             action="store_true" )
    argparser.add_argument ( '-c', '--clean', help='clean all temporary files, then quit',
                             action="store_true" )
    argparser.add_argument ( '-C', '--clean_all', help='clean all temporary files, even Tx directories, then quit',
                             action="store_true" )
    mdefault = "(500,510,10),(100,110,10)"
    argparser.add_argument ( '-m', '--masses', help='mass ranges, comma separated list of tuples. One tuple gives the range for one mass parameter, as (m_first,m_last,delta_m). m_last and delta_m may be ommitted [%s]' % mdefault,
                             type=str, default=mdefault )
    args = argparser.parse_args()
    if args.clean:
        subprocess.getoutput ( "rm -rf mg5cmd* mg5proc* tmp*slha" )
        print ( "Cleaned temporary files." )
        sys.exit()
    if args.clean_all:
        subprocess.getoutput ( "rm -rf mg5cmd* mg5proc* tmp*slha T*jet*" )
        print ( "Cleaned temporary files." )
        sys.exit()
    masses = bakeryHelpers.parseMasses ( args.masses, filterOrder=True )
    nm = len(masses)
    nprocesses = bakeryHelpers.nJobs ( args.nprocesses, nm )
    mg5 = MG5Wrapper( args.nevents, args.topo, args.njets, args.keep )
    # mg5.info( "%d points to produce, in %d processes" % (nm,nprocesses) )
    djobs = int(len(masses)/nprocesses)

    def runChunk ( chunk, pid ):
        for c in chunk:
            mg5.run ( c, pid )

    jobs=[]
    for i in range(nprocesses):
        chunk = masses[djobs*i:djobs*(i+1)]
        if i == nprocesses-1:
            chunk = masses[djobs*i:]
        p = multiprocessing.Process(target=runChunk, args=(chunk,i))
        jobs.append ( p )
        p.start()
    # mg5.run( [ 500, 100 ] )

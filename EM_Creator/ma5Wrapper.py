#!/usr/bin/env python3

"""
.. module:: ma5Wrapper
        :synopsis: code that wraps around MadAnalysis5. Produces the data cards,
                   and runs the ma5 executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil, tempfile, time
import multiprocessing
import bakeryHelpers

class MA5Wrapper:
    def __init__ ( self, topo, njets, rerun, ver="1.7" ):
        """ 
        :param ver: version of ma5
        """
        self.topo = topo
        self.njets = njets
        self.rerun = rerun
        self.ma5install = "./ma5/"
        self.ver = ver
        if not os.path.isdir ( self.ma5install ):
            self.error ( "ma5 install is missing??" )
        self.executable = "bin/ma5"
        if not os.path.exists ( self.ma5install + self.executable ):
            self.info ( "cannot find ma5 installation at %s" % self.ma5install )
            self.exe ( "ma5/make.py" )
        self.templateDir = "templates/"
        self.info ( "initialised" )

    def info ( self, *msg ):
        print ( "%s[ma5Wrapper] %s%s" % ( colorama.Fore.YELLOW, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def debug( self, *msg ):
        pass

    def msg ( self, *msg):
        print ( "[ma5Wrapper] %s" % " ".join ( msg ) )

    def error ( self, *msg ):
        print ( "%s[ma5Wrapper] %s%s" % ( colorama.Fore.RED, " ".join ( msg ), \
                   colorama.Fore.RESET ) )
        sys.exit()

    def writeRecastingCard ( self ):
        """ this method writes the recasting card, which defines which analyses
        are being recast. """
        filename = self.ma5install + "recasting.dat" 
        self.debug ( "writing recasting card %s" % filename )
        if os.path.exists ( filename ):
            os.unlink ( filename )
        templatefile = self.templateDir+'/recasting_card.dat'
        if not os.path.exists ( templatefile ):
            self.error ( "cannot find %s" % templatefile )
        ## for now simply copy the recasting card
        shutil.copy ( templatefile, filename )
        self.info ( "wrote recasting card %s" % filename )

    def writeCommandFile ( self, hepmcfile, process, masses ):
        """ this method writes the commands file for ma5.
        :param hepmcfile: I think thats the input events
        """
        f = open(self.ma5install + "/" + self.commandfile,'w')
        f.write('set main.recast = on\n')
        f.write('set main.recast.card_path = recasting.dat\n' )
        f.write('import '+hepmcfile+'\n')
        f.write('submit ANA_%s\n' % bakeryHelpers.dirName(process,masses)  )
        f.close()

    def run( self, masses, pid=None ):
        """ Run MA5 over an hepmcfile, specifying the process """
        if pid!=None:
            time.sleep(pid*10) ## all the compiling ...
        self.commandfile = tempfile.mktemp ( prefix="ma5cmd", dir="./" )
        self.teefile = tempfile.mktemp ( prefix="ma5", suffix=".run", dir="/tmp" )
        process = "%s_%djet" % ( self.topo, self.njets )
        dirname = bakeryHelpers.dirName ( process, masses )
        summaryfile = "ma5/ANA_%s/Output/CLs_output_summary.dat" % dirname
        if os.path.exists ( summaryfile ) and os.stat(summaryfile).st_size>10:
            print ( "It seems like there is already a summary file %s" % summaryfile )
            if not self.rerun:
                print ( "Skip it." )
                return
        self.writeRecastingCard ()
        # then write command file
        Dir = bakeryHelpers.dirName ( process, masses ) 
        hepmcfile = "%s/Events/run_01/tag_1_pythia8_events.hepmc.gz" % Dir
        hepmcfile = os.path.abspath ( hepmcfile )
        if not os.path.exists ( hepmcfile ):
            print ( "Error cannot find hepmc file at %s" % hepmcfile )
            sys.exit()
        print ( "Found hepmcfile at", hepmcfile )
        self.writeCommandFile( hepmcfile, process, masses )
        # then run madgraph5
        os.chdir ( "ma5/" )
        cmd = "%s -R -s %s 2>&1 | tee %s" % (self.executable, \
                self.commandfile, self.teefile )
        self.exe ( cmd )
        if os.path.exists ( self.commandfile ):
            subprocess.getoutput ( "rm -r %s" % self.commandfile )
        if os.path.exists ( self.teefile ):
            subprocess.getoutput ( "rm -r %s" % self.teefile )
        #shutil.move ( "ANALYSIS_0", "ANA_%s" % Dir )
        os.chdir ( "../" )

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

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='madanalysis5 runner.')
    argparser.add_argument ( '-a', '--analyses', help='analyses, comma separated [atlas_sus_2016_07]',
                             type=str, default="atlas_susy_2016_07" )
    argparser.add_argument ( '-j', '--njets', help='number of ISR jets [0]',
                             type=int, default=0 )
    argparser.add_argument ( '-t', '--topo', help='topology [T2]',
                             type=str, default="T2" )
    mdefault = "all"
    argparser.add_argument ( '-m', '--masses', help='mass ranges, comma separated list of tuples. One tuple gives the range for one mass parameter, as (m_first,m_last,delta_m). m_last and delta_m may be ommitted. "all" means: search for mg5 directories, and consider all. [%s]' % mdefault,
                             type=str, default=mdefault )
    argparser.add_argument ( '-p', '--nprocesses', help='number of process to run in parallel. 0 means 1 per CPU [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-r', '--rerun', help='force rerun, even if there is a summary file already',
                             action="store_true" )
    args = argparser.parse_args()
    if args.masses == "all":
        masses = bakeryHelpers.getListOfMasses ( args.topo, args.njets )
    else:
        masses = bakeryHelpers.parseMasses ( args.masses )
    nm = len(masses)
    nprocesses = bakeryHelpers.nJobs ( args.nprocesses, nm )
    ma5 = MA5Wrapper( args.topo, args.njets, args.rerun )
    # ma5.info( "%d points to produce, in %d processes" % (nm,nprocesses) )
    djobs = int(len(masses)/nprocesses)

    def runChunk ( chunk, pid ):
        for c in chunk:
            ma5.run ( c, pid )

    jobs=[]
    for i in range(nprocesses):
        chunk = masses[djobs*i:djobs*(i+1)]
        if i == nprocesses-1:
            chunk = masses[djobs*i:]
        p = multiprocessing.Process(target=runChunk, args=(chunk,i))
        jobs.append ( p )
        p.start()

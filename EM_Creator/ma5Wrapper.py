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
    def __init__ ( self, topo, njets, rerun, analyses, ver="1.7" ):
        """
        :param ver: version of ma5
        """
        self.topo = topo
        self.njets = njets
        self.analyses = analyses
        self.rerun = rerun
        self.ma5results = "./ma5/"
        self.ma5install = "./ma5.template/"
        self.ver = ver
        if not os.path.isdir ( self.ma5install ):
            self.error ( "ma5 install is missing??" )
            sys.exit()
        self.executable = "bin/ma5"
        if not os.path.exists ( self.ma5install + self.executable ):
            self.info ( "cannot find ma5 installation at %s" % self.ma5install )
            self.exe ( "ma5/make.py" )
        self.templateDir = "templates/"
        # self.info ( "initialised" )

    def info ( self, *msg ):
        print ( "%s[ma5Wrapper] %s%s" % ( colorama.Fore.YELLOW, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def debug( self, *msg ):
        pass

    def msg ( self, *msg):
        print ( "[ma5Wrapper] %s" % " ".join ( msg ) )

    def error ( self, *msg ):
        print ( "%s[ma5Wrapper] Error: %s%s" % ( colorama.Fore.RED, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def writeRecastingCard ( self ):
        """ this method writes the recasting card, which defines which analyses
        are being recast. """
        self.recastfile = tempfile.mktemp ( dir=self.ma5install, prefix="recast" )
        filename = self.recastfile
        # filename = self.ma5install + "recasting.dat"
        self.debug ( "writing recasting card %s" % filename )
        templatefile = self.templateDir+'/recasting_card.dat'
        if not os.path.exists ( templatefile ):
            self.error ( "cannot find %s" % templatefile )
            sys.exit()
        ## for now simply copy the recasting card
        shutil.copy ( templatefile, filename )
        f = open ( filename, "at" )
        recastcard = { "atlas_susy_2016_07": "delphes_card_atlas_exot_2015_03" }
        recastcard["cms_sus_16_033"] = "delphes_card_cms_sus_16_033"
        anas = set(self.analyses.split(","))
        versions = { "atlas_susy_2016_07": "1.2", 
                     "cms_sus_16_033": "1.2" }
        for i in anas:
            print ( "[ma5Wrapper] writing %s in recast card %s" % ( i, filename ) )
            f.write ( "%s         v%s        on    %s.tcl\n" % ( i, versions[i], recastcard[i] ) )
        f.close()
        self.info ( "%s: wrote recasting card %s" % ( time.asctime(), filename ) )

    def unlink ( self, f ):
        if os.path.exists ( f ):
            subprocess.getoutput ( "rm -rf %s" % f )

    def writeCommandFile ( self, hepmcfile, process, masses ):
        """ this method writes the commands file for ma5.
        :param hepmcfile: I think thats the input events
        """
        f = open(self.ma5install + "/" + self.commandfile,'w')
        f.write('set main.recast = on\n')
        filename = self.recastfile.replace(self.ma5install,"./")
        f.write('set main.recast.card_path = %s\n' % filename )
        f.write('import '+hepmcfile+'\n')
        f.write('submit ANA_%s\n' % bakeryHelpers.dirName(process,masses)  )
        f.close()

    def run( self, masses, pid=None ):
        """ Run MA5 over an hepmcfile, specifying the process """
        #if pid!=None:
        #    time.sleep(pid*30) ## all the compiling ...
        self.commandfile = tempfile.mktemp ( prefix="ma5cmd", dir="./" )
        self.teefile = tempfile.mktemp ( prefix="ma5", suffix=".run", dir="/tmp" )
        process = "%s_%djet" % ( self.topo, self.njets )
        dirname = bakeryHelpers.dirName ( process, masses )
        summaryfile = "ma5/ANA_%s/Output/CLs_output_summary.dat" % dirname
        if os.path.exists ( summaryfile ) and os.stat(summaryfile).st_size>10:
            self.msg ( "It seems like there is already a summary file %s" % summaryfile )
            f=open(summaryfile,"rt")
            lines=f.readlines()
            f.close()
            anaIsIn = {}
            analyses = self.analyses.split(",")
            for ana in analyses:
                anaIsIn[ana]=False
            for line in lines:
                for ana in analyses:
                    if ana in line:
                        anaIsIn[ana]=True
            allAnasIn = sum ( anaIsIn.values() ) == len(anaIsIn)
            if allAnasIn and (not self.rerun):
                self.msg ( "%s are in the summary file for %s: skip it." % ( self.analyses, str(masses) ) )
                return
            if not allAnasIn:
                self.msg ( "%s not in summary file: rerun!" % self.analyses )
        Dir = bakeryHelpers.dirName ( process, masses )
        hepmcfile = "%s/Events/run_01/tag_1_pythia8_events.hepmc.gz" % Dir
        hepmcfile = os.path.abspath ( hepmcfile )
        if not os.path.exists ( hepmcfile ):
            self.error ( "cannot find hepmc file %s" % hepmcfile )
            p = hepmcfile.find("Events")
            cmd = "rm -rf %s" % hepmcfile[:p]
            o = subprocess.getoutput ( cmd )
            self.error ( "deleting the folder %s: %s" % ( cmd, o ) )
            return
            # sys.exit()
        # now write recasting card
        self.msg ( "Found hepmcfile at", hepmcfile )
        self.writeRecastingCard ()
        self.writeCommandFile( hepmcfile, process, masses )
        tempdir = "ma5_%s" % Dir
        a = subprocess.getoutput ( "mkdir %s" % tempdir )
        a = subprocess.getoutput ( "cp -r ma5.template/bin ma5.template/madanalysis ma5.template/tools %s" % tempdir )
        a = subprocess.getoutput ( "cp -r %s %s" % ( self.recastfile, tempdir ) )
        a = subprocess.getoutput ( "cp -r ma5.template/%s %s" % ( self.commandfile, tempdir ) )

        # then run MadAnalysis
        os.chdir ( tempdir )
        cmd = "%s -R -s %s 2>&1 | tee %s" % (self.executable, \
                self.commandfile, self.teefile )
        self.exe ( cmd )
        self.unlink ( self.recastfile )
        self.unlink ( "ma5.template/%s" % self.commandfile )
        self.unlink ( self.commandfile )
        self.unlink ( self.teefile )
        source = "ANA_%s" % Dir
        dest = "../ma5/%s" % source
        if os.path.exists ( dest ):
            print ( "[ma5Wrapper] Destination %s exists. I remove it." % dest )
            subprocess.getoutput ( "rm -rf %s" % dest )
        if not os.path.exists ( source ):
            print ( "[ma5Wrapper] Source dir %s does not exist." % source )
        shutil.move ( "ANA_%s" % Dir, "../ma5/" )
        os.chdir ( "../" )
        self.exe ( "rm -rf %s/ma5cmd*" % self.ma5install )
        self.exe ( "rm -rf %s/recast*" % self.ma5install )
        self.exe ( "rm -rf %s" % tempdir )
        # a = subprocess.getoutput ( "rm -rf %s/ma5cmd*" % delf.ma5install )
        # a = subprocess.getoutput ( "rm -rf %s/recast*" % self.ma5install )
        # a = subprocess.getoutput ( "rm -r %s" % tempdir )

    def exe ( self, cmd, maxLength=100 ):
        """ execute cmd in shell
        :param maxLength: maximum length of output to be printed
        """
        self.msg ( "exec: %s/%s" % (os.getcwd(), cmd ) )
        ret = subprocess.getoutput ( cmd )
        ret = ret.strip()
        if len(ret)==0:
            return
        # maxLength=60
        # maxLength=560
        if len(ret)<maxLength:
            self.msg ( " `- %s" % ret )
            return
        self.msg ( " `- %s" % ( ret[-maxLength:] ) )

    def clean ( self ):
        subprocess.getoutput ( "rm -rf ma5.template/recast*" )
        subprocess.getoutput ( "rm -rf ma5.template/ma5cmd*" )
    def clean_all ( self ):
        self.clean()
        subprocess.getoutput ( "rm -rf ma5/ANA*" )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='madanalysis5 runner.')
    argparser.add_argument ( '-a', '--analyses', help='analyses, comma separated [atlas_sus_2016_07]',
                             type=str, default="atlas_susy_2016_07" )
    argparser.add_argument ( '-j', '--njets', help='number of ISR jets [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-t', '--topo', help='topology [T2]',
                             type=str, default="T2" )
    argparser.add_argument ( '-c', '--clean', help='clean all temporary files, then quit',
                             action="store_true" )
    argparser.add_argument ( '-C', '--clean_all', help='clean all temporary files, even results directories, then quit',
                             action="store_true" )
    mdefault = "all"
    argparser.add_argument ( '-m', '--masses', help='mass ranges, comma separated list of tuples. One tuple gives the range for one mass parameter, as (m_first,m_last,delta_m). m_last and delta_m may be ommitted. "all" means: search for mg5 directories, and consider all. [%s]' % mdefault,
                             type=str, default=mdefault )
    argparser.add_argument ( '-p', '--nprocesses', help='number of process to run in parallel. 0 means 1 per CPU [1]',
                             type=int, default=1 )
    argparser.add_argument ( '-r', '--rerun', help='force rerun, even if there is a summary file already',
                             action="store_true" )
    args = argparser.parse_args()
    if args.clean:
        ma5 = MA5Wrapper( args.topo, args.njets, args.rerun, args.analyses )
        ma5.clean()
        sys.exit()
    if args.clean_all:
        ma5 = MA5Wrapper( args.topo, args.njets, args.rerun, args.analyses )
        ma5.clean_all()
        sys.exit()
    if args.masses == "all":
        masses = bakeryHelpers.getListOfMasses ( args.topo, args.njets )
    else:
        masses = bakeryHelpers.parseMasses ( args.masses )
    nm = len(masses)
    nprocesses = bakeryHelpers.nJobs ( args.nprocesses, nm )
    ma5 = MA5Wrapper( args.topo, args.njets, args.rerun, args.analyses )
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

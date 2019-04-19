#!/usr/bin/env python3

"""
.. module:: ma5Wrapper
        :synopsis: code that wraps around MadAnalysis5. Produces the data cards,
                   and runs the ma5 executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil, tempfile
import bakeryHelpers

class MA5Wrapper:
    def __init__ ( self, ver="1.7" ):
        """ 
        :param ver: version of ma5
        """
        self.ma5install = "./ma5/"
        self.ver = ver
        if not os.path.isdir ( self.ma5install ):
            self.error ( "ma5 install is missing??" )
        self.executable = "bin/ma5"
        if not os.path.exists ( self.ma5install + self.executable ):
            self.info ( "cannot find ma5 installation at %s" % self.ma5install )
            self.exe ( "ma5/make.py" )
        self.templateDir = "templates/"
        # self.commandfile = "ma5commands.txt"
        self.commandfile = tempfile.mktemp ( prefix="ma5", dir="./" )
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
        f.write('set main.recast.card_path = recasting_card.dat\n' )
        f.write('import '+hepmcfile+'\n')
        f.write('submit ANA_%s\n' % bakeryHelpers.dirName(process,masses)  )
        f.close()

    # def run( self, hepmcfile, topo ):
    def run( self, process, masses, topo ):
        """ Run MA5 over an hepmcfile, specifying the process """
        self.writeRecastingCard ()
        # then write command file
        Dir = bakeryHelpers.dirName ( process, masses ) 
        hepmcfile = "%s/Events/run_01/tag_1_pythia8_events.hepmc.gz" % Dir
        hepmcfile = os.path.abspath ( hepmcfile )
        print ( "hepmcfile at", hepmcfile )
        if not os.path.exists ( hepmcfile ):
            print ( "Error cannot find hepmc file at %s" % hepmcfile )
            sys.exit()
        self.writeCommandFile( hepmcfile, process, masses )
        # then run madgraph5
        os.chdir ( "ma5/" )
        cmd = "%s -R -s %s 2>&1 | tee /tmp/ma5.run" % (self.executable, \
                self.commandfile )
        self.exe ( cmd )
        if os.path.exists ( self.commandfile ):
            subprocess.getoutput ( "rm -r %s" % self.commandfile )
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
    ma5 = MA5Wrapper()
    process = "T2tt_1jet"
    topo = "T2tt"
    masses= [500, 100]
    ma5.run( process, masses, topo )
    # ma5.run( "T2tt_1jet/Events/run_01/tag_1_pythia8_events.hepmc.gz", "T2tt" )

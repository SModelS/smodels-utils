#!/usr/bin/env python3

"""
.. module:: mg5Wrapper
        :synopsis: code that wraps around MadGraph5. Produces the data cards,
                   and runs the mg5 executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
"""

import os, sys, colorama, subprocess, shutil

class MG5Wrapper:
    def __init__ ( self, ver="2_6_5" ):
        """ 
        :param ver: version of mg5
        """
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
                          'NEVENTS': '10', 'MAXJETFLAVOR': '5', 
                          'PDFLABEL': 'cteq6l1', 'XQCUT': '50' } #, 'qcut': '90' }
        self.commandfile = "mg5commands.txt"
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

    def writeCommandFile ( self, process = "" ):
        """ this method writes the commands file for mg5.
        :param process: fixme (eg T2_11jet)
        """
        f = open(self.commandfile,'w')
        f.write('set automatic_html_opening False\n' )
        f.write('launch '+ process+'\n')
        f.write('shower=Pythia8\n')
        f.write('detector=OFF\n')
        #f.write('detector=Delphes\n')
        #f.write('pythia=ON\n')
        #f.write('madspin=OFF\n')
        f.write('0\n')
        f.write('0\n')
        f.close()

    def run( self, slhaFile, process ):
        """ Run MG5 over an slhaFile, specifying the process """
        # first write pythia card
        self.writePythiaCard ( process=process )
        # then write command file
        self.writeCommandFile( process=process )
        # then run madgraph5
        self.execute ( slhaFile, process )

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

    def execute ( self, slhaFile, process ):
        templatefile = self.templateDir + '/MG5_Process_Cards/'+process+'.txt'
        if not os.path.isfile( templatefile ):
            self.error ( "The process card %s does not exist." % templatefile )
        self.info ( "run mg5 for %s" % process )
        cmd = "%s %s" % ( self.executable, templatefile )
        self.exe ( cmd )
        ## copy slha file
        shutil.copyfile(slhaFile, process+'/Cards/param_card.dat' )
        shutil.copyfile("run_card.dat", process+'/Cards/run_card.dat' )
        if (os.path.isdir(process+'/Events/run_01')):
            shutil.rmtree(process+'/Events/run_01')
        cmd = "%s %s" % ( self.executable, self.commandfile )
        self.exe ( cmd )


if __name__ == "__main__":
    mg5 = MG5Wrapper()
    process = "T2tt_1jet"
    # process = "T2tt_1jet"
    mg5.run( "slha/T2tt.slha", process )

#!/usr/bin/env python3

"""
.. module:: cutlangWrapper
        :synopsis: code that wraps around cutlang. Produces the data cards,
                   and runs the cutlang executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
.. moduleauthor:: Jan Mrozek <jmrozek@protonmail.ch>
"""
# TODO: Make separate Delphes wrapper?
# TODO: Make nested class for directories that would check if it exists and is
# dir: os.path.exists(dirName) and os.path.isdir(dirName) ?
# TODO: Add exception mechanism to exe.
# TODO: Remove the directory if makefile not present?

# Standard library imports
import os                  # For path
import sys                 # For exit()
import colorama            # For output colors (in msg, error, ...)
import subprocess          # For Popen in exe method
import shutil             # For move()
import tempfile            # FIXME: Either remove or implement
import  re                 # For delphes card picker
from datetime import date  # For timestamp of embaked files
import multiprocessing     # Used when run as __main__

# 3 party imports
import ROOT                # To parse CutLang output

# local imports
import bakeryHelpers       # For dirnames

class cutlangWrapper:
    OUTPUT_DIR  = "./cutlang_output"
    OUTPUT_FILE = "./cutlang_output/CutLang_efficiencies.embaked"
    CUTLANGINPUT = "./cutlang_output/analysis.root"

    CUTLANGRESULTS = "./CutLang/results"
    TEMPLATEDIR = "templates/"
    # CLA_output = "./CutLang/runs/histoOut-analysis.root"
    CLA_output = "./CutLang/runs/histoOut-CMS-SUS-19-007_CutLang.root"

    def __init__ ( self, topo, njets, rerun, analyses):
        """
        If not already present, clones and builds Delphes, CutLang and ADLLHC Analyses.
        Prepares output directories.

        :param topo:    string  SMS topology (see https://smodels.github.io/docs/SmsDictionary )
        :param njets:   int     Number of jets
        :param rerun:   boo     True for rerunning the analyses already done
        :param analyses list    List of analyses to be done
                           (specified as string, see https://smodels.github.io/docs/ListOfAnalyses)
        """
        # Cutlang vars
        self.cutlanginstall = "./CutLang/"
        self.cutlang_executable = "./CutLang/CLA/CLA.exe"
        # Directory where the CutLang will run
        self.cutlang_run_dir = "./CutLang/runs"
        self.cutlang_script = "CLA.sh"

        # ADLLHCAnalysis vars
        self.adllhcanalyses = "./CutLang/ADLLHCanalyses"

        # Delphes vars
        self.delphesinstall = "./delphes/"

        # General vars
        self.njets = njets
        self.topo = topo
        self.analyses = analyses
        self.rerun = rerun

        # FIXME: Redo this:
        if not os.path.isdir(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)

        # =====================
        #      Cutlang Init
        # =====================
        # Check if Cutlang dir is present and if not, attempt to clone it from github
        if not os.path.isdir ( self.cutlanginstall ):
            self.info( "cutlang directory missing, download from github?")
            if self.__confirmation("Download from github? (yes/no):"):
                args = ['git', 'clone', 'https://github.com/unelg/CutLang']
                self.exe(args, exit_on_fail=True)
            else:
                self.error("No CutLang dir. Exiting.")
        # if there is no executable, compile it
        if not os.path.exists (self.cutlang_executable):
            self.info ( "cannot find cutlang installation at %s" % self.cutlanginstall )
            compile_path = os.path.abspath(self.cutlanginstall + "CLA/")
            # Check for existence of makefile, if not present - rm CutLang
            # directory and exit.
            # TODO: Remove the directory?
            makefile_path = os.path.join(compile_path, "Makefile")
            if not os.path.isfile(makefile_path):
                self.error("No executable and no Makefile. Bailin' it.")
                sys.exit()
            self.info("Compiling CutLang...")
            args = ['make']
            self.exe(args, cwd = compile_path, exit_on_fail = True)
        self.info("CutLang initialisation finished.")

        # ==============================
        #      ADL LHC Analyses Init
        # ==============================
        # Check if ADLLHCAnalyses dir is present and if not, attempt to clone it from github
        if not os.path.exists(self.adllhcanalyses):
            os.makedirs(self.adllhcanalyses)
        if not os.path.isdir(self.adllhcanalyses):
            self.error("ADL LHC Analyses path is not a direcotry, exiting.")
            sys.exit()
        if len(os.listdir(self.adllhcanalyses)) == 0:
            args = ["rm", "-rf", self.adllhcanalyses]
            self.exe(args)
            args = ["git", "clone", "https://github.com/ADL4HEP/ADLLHCanalyses"]
            self.exe(args, cwd=os.path.dirname(self.adllhcanalyses), exit_on_fail=True)
        self.info("ADLLHC Analyses initialisation finished.")

        # ====================
        #      Delphes Init
        # ====================
        # Check if Delphes dir is present and if not, attempt to clone it from github
        if not os.path.isdir ( self.delphesinstall ):
            self.info( "Delphes directory missing, download from github?")
            if self.__confirmation("Download from github? (yes/no):"):
                args = ['git', 'clone', 'https://github.com/delphes/delphes']
                self.exe(args, exit_on_fail = True)
            else:
                self.error("No Delphes dir. Exiting.")
        # if there is no executable, compile it
        self.delphes_exe = os.path.abspath(self.delphesinstall + "DelphesHepMC")
        if not os.path.exists (self.delphes_exe):
            self.info ( "cannot find delphes installation at %s" % self.delphesinstall )
            compile_path = os.path.abspath(self.delphesinstall)
            # Check for existence of makefile, if not present - rm Delphes
            # directory and exit.
            makefile_path = os.path.join(compile_path, "Makefile")
            if not os.path.isfile(makefile_path):
                self.error("No executable and no Makefile. Bailin' it.")
                sys.exit()
            self.info("Compiling...")
            args = ['make']
            self.exe(args, cwd = compile_path)
        self.info("initialised")

    def info ( self, *msg ):
        """Print yellow info message"""
        print ( "%s[cutlangWrapper] %s%s" % ( colorama.Fore.YELLOW, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def debug( self, *msg ):
        """Not implemented"""
        pass

    def msg ( self, *msg):
        """Print normal message"""
        print ( "[cutlangWrapper] %s" % " ".join ( msg ) )

    def error ( self, *msg ):
        """Print red error message"""
        print ( "%s[cutlangWrapper] Error: %s%s" % ( colorama.Fore.RED, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def __delete_dir ( self, f ):
        if os.path.exists ( f ):
            subprocess.getoutput ( "rm -rf %s" % f )

    def pickCutLangFile (self, a_name):
        """ Returns absolute path to ADLLHC Analysis file. If not available raises error. """
        a_name = a_name.replace("_", "-")
        cla_path = os.path.join(self.adllhcanalyses, a_name.upper(), a_name.upper() + "_CutLang.adl")
        if os.path.isfile(cla_path):
            self.msg(f"Using CutLang file {cla_path}.")
            return os.path.abspath(cla_path)
        else:
            raise Exception(f"No analysis file found for analysis {a_name} found at: \n" + cla_path)

    def extract_efficiencies(self, masses, filename):
        """ Extracts the efficiencies from CutLang output..."""

        rootFile = ROOT.TFile(filename)
        if rootFile == None:
            self.error("Cannot find CutLang results, exiting.")
            sys.exit()
        rootTmp  = ROOT.TH1D()
        with open(self.OUTPUT_FILE, "w") as f:
            f.write("{" + str(masses) + ": {")
            nevents = 0
            print([x.ReadObj().GetName() for x in rootFile.GetListOfKeys()])
            for x in rootFile.GetListOfKeys():
                x.ReadObj().GetObject("cutflow", rootTmp)
                name = x.ReadObj().GetName()
                print(name)
                if name == 'baseline':
                    pass
                    # continue
                f.write("".join(["'", str(x.ReadObj().GetName()),"': "]))
                s = rootTmp.GetNbinsX()
                if rootTmp[2] == 0:
                    f.write("NaN")
                f.write(str(rootTmp[(s-1)]/rootTmp[2]) + ', ')
                print(rootTmp[(s-1)]/rootTmp[2])
                nevents = rootTmp[2]
            f.write(f"'__t__':'{date.today().strftime('%Y-%m-%d_%H:%M:%S')}', ")
            f.write(f"'__nevents__':{nevents}")
            f.write("}")
            f.write("}")

    def __get_cla_out_filename(self, inputname):
        """ Returns the name of CLA output file"""
        outfile = os.path.join(self.cutlang_run_dir,
                               "histoOut-" + os.path.basename(inputname).split(".")[0] + ".root")
        self.info(f"Searching for CLA output at:\n{outfile}")
        if os.path.isfile(outfile):
            return outfile
        else:
            self.error("Could not find CLA output file. Aborting.")
            sys.exit()


    def run(self, masses, hepmcfile, pid=None):
        """ TODO: Write some commentary.


            input.hepmc --> Delphes --> output.root --┬-> CutLang --> eff.embaked
                                        CutLang.edl --┘
        """
        # for stdout
        process = "%s_%djet" % (self.topo, self.njets)
        dirname = bakeryHelpers.dirName (process, masses)

        # For Analysis summary
        summaryfile = f"ANA_{dirname}/Output/CLs_output_summary.dat"
        if os.path.exists ( summaryfile ):
            if os.stat(summaryfile).st_size>10:
                self.msg (f"It seems like there is already a summary file {summaryfile}")
                f=open(summaryfile,"rt")
                lines=f.readlines()
                f.close()
                anaIsIn = False
                for line in lines:
                    if self.analyses in line:
                        anaIsIn = True
                if anaIsIn and (not self.rerun):
                    self.msg ( "%s is in the summary file for %s: skip it." % ( self.analyses, str(masses) ) )
                    return
                if not anaIsIn:
                    self.msg ( "%s not in summary file: rerun!" % self.analyses )
                    f.write(self.analyses + "\n")
            else:
                with open(summaryfile, "w") as f:
                    f.write(self.analyses + "\n")
        else:
            summary_dir = os.path.dirname(summaryfile)
            if not os.path.exists(summary_dir):
                os.makedirs(summary_dir)
            with open(summaryfile, "w") as f:
                f.write(self.analyses + "\n")


        # ======================
        #        Delphes
        # ======================
        if not os.path.isfile(hepmcfile):
            self.error (f"cannot find hepmc file {hepmcfile}, exiting.")
            sys.exit()
        self.msg ("Found hepmcfile at", hepmcfile)
        delphes_card = self.__pick_delphes_card()
        output_file = self.CUTLANGINPUT
        self.info("Running delphes.")
        args = [self.delphes_exe, delphes_card, output_file, hepmcfile]
        self.exe(args)
        self.info("Delphes finished.")

        # ======================
        #        CutLang
        # ======================
        # FIXME: copy CutLang into temporary directory?

        # FIXME: redo cutlang invocation, file passing...
        cla_input = os.path.abspath(self.CUTLANGINPUT)
        self.cutlang_script = os.path.abspath("./CutLang/runs/CLA.sh")
        cutlangfile = self.pickCutLangFile(self.analyses)

        cmd = [self.cutlang_script, cla_input, "DELPHES", "-i", cutlangfile]
        self.info("Running CLA")
        self.exe(cmd, cwd=("/home/jan/prog/smodels-utils/EM_Creator/CutLang/runs/"))
        self.info("CLA finished.")



        # ====================
        #  Postprocessing
        # ====================

        CLA_output = self.__get_cla_out_filename(cutlangfile)
        self.extract_efficiencies(masses, CLA_output)

        # self.__delete_dir(self.recastfile)
        # self.__delete_dir("cutlang.template/%s" % self.cutlangfile)
        # self.__delete_dir(self.cutlangfile)
        # self.__delete_dir(self.teefile)
        source = "ANA_%s" % dirname
        dest = "../cutlang/%s" % source
        if os.path.exists ( dest ):
            print ( "[cutlangWrapper] Destination %s exists. I remove it." % dest )
            subprocess.getoutput ( "rm -rf %s" % dest )
        if not os.path.exists ( source ):
            print ( "[cutlangWrapper] Source dir %s does not exist." % source )
        # shutil.move ( f"ANA_{dirname}", "../cutlang/" )
        self.exe("rm -rf %s/cutlangcmd*" % self.cutlanginstall )
        self.exe("rm -rf %s/recast*" % self.cutlanginstall )
        # self.exe("rm -rf %s" % tempdir )
        # a = subprocess.getoutput ( "rm -rf %s/cutlangcmd*" % self.cutlanginstall )
        # a = subprocess.getoutput ( "rm -rf %s/recast*" % self.cutlanginstall )
        # a = subprocess.getoutput ( "rm -r %s" % tempdir )

    def exe ( self, cmd, maxLength=100, cwd=None, exit_on_fail=False):
        """ execute cmd in shell
        :param maxLength: maximum length of output to be printed,
                          if == -1 then all output will be printed
        """
        if cwd == None:
            directory = os.getcwd()
        else:
            directory = cwd
        self.msg ( f'exec: {directory} $$ {" ".join(cmd)}' )
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        out, err = proc.communicate()
        print(out.decode('utf-8'))
        if not (err == None or err == 0):
            self.error(f"Executed process: \n{' '.join(cmd)}\nin directory:\n{directory}\nproduced an error value {err}.")
            if exit_on_fail == True:
                pass
                # sys.exit()
        # out = out.strip()
        # if len(out)==0:
        #     pass
        # elif len(out)<maxLength:
        #     self.msg ( " `- %s" % out )
        #     outurn
        # else:
        #     self.msg ( " `- %s" % ( out[-maxLength:] ) )
        return err

    def __pick_delphes_card(self):
        if not re.search("atlas", self.analyses) == None:
            return os.path.abspath("./delphes/cards/delphes_card_ATLAS.tcl")
        elif not re.search("cms", self.analyses) == None:
            return os.path.abspath("./delphes/cards/delphes_card_CMS.tcl")
        else:
            self.error(f"Could not find a suitable Delphes card for analysis {self.analyses}. Exiting.")
            sys.exit()


    def clean ( self ):
        subprocess.getoutput ( "rm -rf cutlang.template/recast*" )
        subprocess.getoutput ( "rm -rf cutlang.template/cutlangcmd*" )
    def clean_all ( self ):
        self.clean()
        subprocess.getoutput ( "rm -rf cutlang/ANA*" )
    def __confirmation(self, text):
        return True

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='cutlang runner.')
    argparser.add_argument ( '-a', '--analyses', help='analyses, comma separated [atlas_sus_2016_07]',
                             type=str, default="atlas_susy_2016_07" )
    argparser.add_argument ( '-d', '--hepmcfile', help='hepmcfile to be used as input for Delphes',
                             type=str, default="input.hepmc" )
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
        cutlang = cutlangWrapper( args.topo, args.njets, args.rerun, args.analyses )
        cutlang.clean()
        sys.exit()
    if args.clean_all:
        cutlang = cutlangWrapper( args.topo, args.njets, args.rerun, args.analyses )
        cutlang.clean_all()
        sys.exit()
    if args.masses == "all":
        masses = bakeryHelpers.getListOfMasses ( args.topo, args.njets )
    else:
        # FIXME: make parseMasses work
        # masses = bakeryHelpers.parseMasses ( args.masses )
        masses = (100, 110, 10)
    # nm = len(masses)
    # nprocesses = bakeryHelpers.nJobs ( args.nprocesses, nm )
    cutlang = cutlangWrapper( args.topo, args.njets, args.rerun, args.analyses )
    cutlang.run(masses, args.hepmcfile)
    # cutlang.info( "%d points to produce, in %d processes" % (nm,nprocesses) )
    #djobs = int(len(masses)/nprocesses)

    #def runChunk ( chunk, pid ):
    #    for c in chunk:
    #        cutlang.run ( c, pid )

    #jobs=[]
    #for i in range(nprocesses):
    #    chunk = masses[djobs*i:djobs*(i+1)]
    #    if i == nprocesses-1:
    #        chunk = masses[djobs*i:]
    #    p = multiprocessing.Process(target=runChunk, args=(chunk,i))
    #    jobs.append ( p )
    #    p.start()

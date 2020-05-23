#!/usr/bin/env python3

"""
.. module:: CutLangWrapper
        :synopsis: code that wraps around cutlang. Produces the data cards,
                   and runs the cutlang executable.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
.. moduleauthor:: Jan Mrozek <jmrozek@protonmail.ch>

..directory structure::
    EM_Creator --┬-CutLang---------┬-runs ~ dir with running script (CLA.sh)
                 |                 +-CLA  ~ dir with executable (CLA.exe)
                 |                 + ADLLHCAnalysis ~ contains adl files for analyses
                 +-cutlang_wrapper-┬-ANA_*-┬-output-┬-efficiencies.embaked
                 |                 |       |        +-detected.root
                 |                 |       |        +-CL_output_summary.dat
                 |                 |       |        +-log_<time>.txt
                 |                 |       +-temp---┬-hepmcfile.hepmc ~ if it was gzipped
                 |                 +-logs--+log_<time>.txt
                 +-Delphes---------┬-DelphesHepMC ~ delphes executable
                                   +-cards ~ dir with delphes configuration cards
"""
# TODO: Adapt for paralelisation.
# TODO: Make separate Delphes wrapper?
# TODO: Add exception mechanism to exe.
# TODO: Finish directory structure picture...
# TODO: Debug levels?
# TODO: Maybe add same time to logs and embaked?
# FIXME: Refactor postprocessing
# FIXME: Remove the directory if makefile not present
# FIXME: Print only last n lines of exe output.
# FIXME: Instead of exiting, raise exceptions?
# FIXME: Adapt the getmasses scheme to CLA wrapper


# Standard library imports
import os                      # For path
import sys                     # For exit()
import colorama                # For output colors (in msg, error, ...)
import subprocess              # For Popen in exe method
import shutil                  # For move(), FIXME: remove?
import tempfile                # FIXME: Either remove or implement
import  re                     # For delphes card picker
import multiprocessing         # Used when run as __main__
import gzip                    # For decompression of hepmc file
from datetime import datetime  # For timestamp of embaked files

# 3 party imports
import ROOT                # To parse CutLang output

# local imports
import bakeryHelpers       # For dirnames

class CutLangWrapper:

    GZIP_BLOCK = 1 << 24 # Block to decompress gzipped file, ~ 16 MB

    def __init__ ( self, topo, njets, rerun, analyses, auto_confirm = True):
        """
        If not already present, clones and builds Delphes, CutLang and ADLLHC Analyses.
        Prepares output directories.

        :param topo:    string  SMS topology (see https://smodels.github.io/docs/SmsDictionary )
        :param njets:   int     Number of jets
        :param rerun:   boo     True for rerunning the analyses already done
        :param analyses list    List of analyses to be done
                           (specified as string, see https://smodels.github.io/docs/ListOfAnalyses)
        """
        # General vars
        self.njets = njets
        self.topo = topo
        self.analyses = self.__standardise_analysis(analyses)
        self.rerun = rerun
        self.auto_confirm = auto_confirm


        # base output directory
        self.base_dir = Directory(f"cutlang_wrapper/{self.analyses}", make = True)
        self.tmp_dir = Directory(os.path.join(self.base_dir.get(), "temp"), make = True)
        time = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        self.initlog = os.path.join(self.tmp_dir.get(), "log_" + time + ".txt")
        self.__delete_dir(self.initlog)

        # Cutlang vars
        self.cutlanginstall = "./CutLang/"
        self.cutlang_executable = "./CutLang/CLA/CLA.exe"
        self.cutlang_run_dir = "./CutLang/runs" # Directory where the CutLang will run
        self.cutlang_script = "CLA.sh"

        # ADLLHCAnalysis vars
        self.adllhcanalyses = "./CutLang/ADLLHCanalyses"

        # Delphes vars
        self.delphesinstall = "./delphes/"

        # =====================
        #      Cutlang Init
        # =====================
        # Check if Cutlang dir is present and if not, attempt to clone it from github
        if not os.path.isdir ( self.cutlanginstall ):
            self.__info( "cutlang directory missing, download from github?")
            if self.__confirmation("Download from github? (yes/no):"):
                args = ['git', 'clone', 'https://github.com/unelg/CutLang']
                self.exe(args, exit_on_fail=True, logfile = self.initlog)
            else:
                self.__error("No CutLang dir. Exiting.")
                sys.exit()

        # if there is no executable, compile it
        if not os.path.exists (self.cutlang_executable):
            self.__info ( "cannot find cutlang installation at %s" % self.cutlanginstall )
            compile_path = os.path.abspath(self.cutlanginstall + "CLA/")
            # Check for existence of makefile, if not present exit
            makefile_path = os.path.join(compile_path, "Makefile")
            if not os.path.isfile(makefile_path):
                self.__error("No executable and no Makefile. Bailin' it.")
                sys.exit()
            self.__info("Compiling CutLang...")
            args = ['make']
            self.exe(args, cwd = compile_path, exit_on_fail = True, logfile = self.initlog)
        self.__info("CutLang initialisation finished.")

        # ==============================
        #      ADL LHC Analyses Init
        # ==============================
        # Check if ADLLHCAnalyses dir is present and if not, attempt to clone it from github
        if not os.path.exists(self.adllhcanalyses):
            os.makedirs(self.adllhcanalyses)
        if not os.path.isdir(self.adllhcanalyses):
            self.__error("ADL LHC Analyses path is not a direcotry, exiting.")
            sys.exit()
        if len(os.listdir(self.adllhcanalyses)) == 0:
            args = ["rm", "-rf", self.adllhcanalyses]
            self.exe(args)
            args = ["git", "clone", "https://github.com/ADL4HEP/ADLLHCanalyses"]
            self.exe(args, cwd=os.path.dirname(self.adllhcanalyses),
                     exit_on_fail=True, logfile = self.initlog)
        self.__info("ADLLHC Analyses initialisation finished.")

        # ====================
        #      Delphes Init
        # ====================
        # Check if Delphes dir is present and if not, attempt to clone it from github
        if not os.path.isdir ( self.delphesinstall ):
            self.__info( "Delphes directory missing, download from github?")
            if self.__confirmation("Download from github? (yes/no):"):
                args = ['git', 'clone', 'https://github.com/delphes/delphes']
                self.exe(args, exit_on_fail = True, logfile = self.initlog)
            else:
                self.__error("No Delphes dir. Exiting.")
        # if there is no executable, compile it
        self.delphes_exe = os.path.abspath(self.delphesinstall + "DelphesHepMC")
        if not os.path.exists (self.delphes_exe):
            self.__info ( "Cannot find delphes installation at %s" % self.delphesinstall )
            compile_path = os.path.abspath(self.delphesinstall)
            # Check for existence of makefile, if not present exit
            makefile_path = os.path.join(compile_path, "Makefile")
            if not os.path.isfile(makefile_path):
                self.__error("No executable and no Makefile. Bailin' it.")
                sys.exit()
            self.__info("Compiling Delphes...")
            args = ['make']
            self.exe(args, cwd = compile_path, exit_on_fail = True, logfile = self.initlog)
        self.__info("Delphes initialised.")
        self.__info("Initialisation complete.")


    def pickCutLangFile (self, a_name):
        """ Returns absolute path to ADLLHC Analysis file. If not available raises error. """
        a_name = a_name.replace("_", "-")
        cla_path = os.path.join(self.adllhcanalyses, a_name.upper(), a_name.upper() + "_CutLang.adl")
        if os.path.isfile(cla_path):
            self.__msg(f"Using CutLang file {cla_path}.")
            return os.path.abspath(cla_path)
        else:
            raise Exception(f"No analysis file found for analysis {a_name} found at: \n" + cla_path)

    def extract_efficiencies(self, cla_out, cla_file):
        """ Extracts the efficiencies from CutLang output.
            :param masses:    mass n-tuple
            :param cla_out:  .root file output of CLA
            :param cla_file:  .adl file specifying CutLang regions
        """

        # open the ROOT file
        rootFile = ROOT.TFile(cla_out)
        if rootFile == None:
            self.__error("Cannot find CutLang results at {cla_out}.")
        # temporary TH1D structure to write results in

        rootTmp  = ROOT.TH1D()
        nevents = [] # list of starting numbers of events
        entries = "" # efficiency entries for output
        contains_eff = False # Whether this root file yielded an efficiencies

        self.__debug("Objects found in CutLang results:")
        self.__debug(str([x.ReadObj().GetName() for x in rootFile.GetListOfKeys()]))

        # Traverse all keys in ROOT file
        for x in rootFile.GetListOfKeys():
            # FIXME: Try to remove continue from here (2x)
            x = x.ReadObj()
            if isinstance(x, ROOT.TDirectoryFile):
                keys = [y.ReadObj().GetName() for y in x.GetListOfKeys()]
                # cutflow ~ the event number histogram
                if "cutflow" not in keys:
                    self.__info(f"Cutflow not in objects in {x.GetName()} in {cla_out}")
                    continue
                x.GetObject("cutflow", rootTmp)
                rname = x.GetName()
                if rname in {'baseline', 'presel'}:
                    continue
                entry = "".join(["'", rname, "': "])
                s = rootTmp.GetNbinsX()
                if rootTmp[2] == 0:
                    entries += "NaN"
                    nevents.append(0)
                    continue
                # rootTmp[2] == number of all events
                entry += str(rootTmp[(s-1)]/rootTmp[2]) + ', '
                self.__debug(entry)
                nevents.append(rootTmp[2])
                entries += entry
                contains_eff = True
                if "bincounts" in keys:
                    self.__info(f"Found bins in {rname} section.")
                    x.GetObject("bincounts", rootTmp)
                    nbins = rootTmp.GetNbinsX()
                    for i in range(nbins):
                        bin_name = rootTmp.GetXaxis().GetBinLabel(i)
                        # bin_name = bin_name.replace("[","").replace("]","")
                        bin_name = "_".join([rname, bin_name.replace(" ", "_")])
                        entry = "".join(["'", bin_name, "': "])
                        self.__debug(f"bin no {rootTmp[i]} nevents: {nevents[-1]}.")
                        entry += str(rootTmp[i]/nevents[-1]) + ', '
                        entries += entry
            else:
                self.__debug(f"{x.GetName()} is not a Directory File.")
                self.__debug(f"{x.GetName()} is of type {type(x)}")
            # entry ~ data point to write into efficiency map
        if contains_eff == False:
            self.__error(f"No efficiencies found in file {cla_out}.")
        return entries, nevents

    def get_cla_out_filename(self, inputname):
        """ Returns the name of CLA output file"""
        outfile = os.path.join(self.cutlang_run_dir,
                               "histoOut-" + os.path.basename(inputname).split(".")[0] + ".root")
        self.__info(f"Searching for CLA output at:\n{outfile}")
        if os.path.isfile(outfile):
            return outfile
        else:
            self.__error("Could not find CLA output file. Aborting.")
            # sys.exit()

    def run(self, mass, hepmcfile, pid=None):
        """ TODO: Write some commentary.


            input.hepmc --> Delphes --> output.root --┬-> CutLang --> eff.embaked
                                        CutLang.edl --┘
        """
        dirname = f"{self.topo}_{self.njets}jet"
        ana_dir = Directory(os.path.join(self.base_dir.get(), f"ANA_{dirname}"), make = True)
        out_dir = Directory(os.path.join(ana_dir.get(), "output"), make = True)
        tmp_dir = Directory(os.path.join(ana_dir.get(), "temp"), make = True)
        time = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        logfile = os.path.join(tmp_dir.get(), "log_" + time + ".txt")
        self.__delete_dir(logfile)

        self.__info(f"Writing output into directory {ana_dir.get()} .")
        self.__info(f"Masses are {mass}")

        # Decompress hepmcfile if necessary
        if ".gz" in hepmcfile:
            hepmcfile = self.__decompress(hepmcfile, tmp_dir.get())

        # Check if the analysis has been done already
        summaryfile = os.path.join(out_dir.get(), "CL_output_summary.dat")
        if os.path.exists ( summaryfile ):
            if os.stat(summaryfile).st_size>10:
                self.__msg (f"It seems like there is already a summary file {summaryfile}")
                f=open(summaryfile,"w+")
                lines=f.readlines()
                anaIsIn = False
                for line in lines:
                    if self.analyses in line:
                        anaIsIn = True
                if anaIsIn and (not self.rerun):
                    self.__msg ( "%s is in the summary file for %s: skip it." % ( self.analyses, str(mass) ) )
                    return
                if not anaIsIn:
                    self.__msg ( "%s not in summary file: rerun!" % self.analyses )
                    f.write(self.analyses + "\n")
                f.close()
            else:
                with open(summaryfile, "w") as f:
                    f.write(self.analyses + "\n")
        else:
            summary_dir = os.path.dirname(summaryfile)
            with open(summaryfile, "w") as f:
                f.write(self.analyses + "\n")


        # ======================
        #        Delphes
        # ======================
        # set input/output paths
        if not os.path.isfile(hepmcfile):
            self.__error (f"cannot find hepmc file {hepmcfile}, exiting.")
            sys.exit()
        self.__msg ("Found hepmcfile at", hepmcfile)
        delphes_card = self.__pick_delphes_card()
        # delph_out = os.path.join(tmp_dir.get(), "-".join([self.analyses, str(mass), "delphes-out"])+".root")
        # FIXME: put this to tmp_dir
        delph_out = os.path.join(tmp_dir.get(), "delphes_out.root")

        # Remove output file if already exists
        if os.path.exists(delph_out):
            self.__info(f"Removing {delph_out}.")
            args = ["rm", delph_out]
            self.exe(args, logfile = logfile)


        # run delphes
        self.__info("Running delphes.")
        args = [self.delphes_exe, delphes_card, delph_out, hepmcfile]
        self.exe(args, logfile = logfile)
        self.__info("Delphes finished.")

        # ======================
        #        CutLang
        # ======================
        # Prepare input/output paths
        cla_input = os.path.abspath(delph_out)
        self.cutlang_script = os.path.abspath("./CutLang/runs/CLA.sh")
        cutlangfile = self.pickCutLangFile(self.analyses)

        # run CutLang
        cmd = [self.cutlang_script, cla_input, "DELPHES", "-i", cutlangfile]
        self.__info("Running CLA")
        self.exe(cmd, cwd=self.cutlang_run_dir, logfile = logfile)
        self.__info("CLA finished.")

        # ====================
        #  Postprocessing
        # ====================
        # efficiency file
        effi_file = os.path.join(out_dir.get(), self.__get_embaked_name(self.analyses, self.topo))
        # CLA results in .root filE
        CLA_output = self.get_cla_out_filename(cutlangfile)
        nevents = []
        entries = ""
        for filename in os.listdir(self.cutlang_run_dir):
            if filename.startswith("histoOut-BP") and filename.endswith(".root"):
                filename = os.path.join(self.cutlang_run_dir, filename)
                tmp_entries, tmp_nevents = self.extract_efficiencies(filename, cutlangfile)
                nevents += tmp_nevents
                entries += tmp_entries
                shutil.move(filename, os.path.join(tmp_dir.get(), os.path.basename(filename)))
        self.__debug(f"Nevents: {nevents}")
        if len(set(nevents)) > 1:
            self.__error("Number of events before selection is not constant in all regions:")
            self.__error(f"Numbers of events: {nevents}")
            self.__error(f"Using the value: {nevents[0]}")
        with open(effi_file, "w") as f:
            f.write("{" + str(mass) + ": {")
            f.write(entries)
            f.write(f"'__t__':'{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}', ")
            f.write(f"'__nevents__':{nevents[0]}")
            f.write("}")
            f.write("}")

    def exe(self, cmd, logfile = None, maxLength=100, cwd=None, exit_on_fail=False):
        """ execute cmd in shell
        :param maxLength: maximum length of output to be printed,
                          if == -1 then all output will be printed
        """
        if cwd == None:
            directory = os.getcwd()
        else:
            directory = cwd
        self.__msg ( f'exec: {directory} $$ {" ".join(cmd)}' )
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        print(out.decode('utf-8'))
        print(err.decode('utf-8'))
        proc.wait()
        if not logfile == None:
            with open(logfile, "a") as log:
                log.write(out.decode('utf-8'))
                log.write(err.decode('utf-8'))
        if not (proc.returncode == 0):
            self.__error(f"Executed process: \n{' '.join(cmd)}\n\nin"
                       f" directory:\n{directory}\n\nproduced an error\n\n"
                       f"value {proc.returncode}.")
            if exit_on_fail == True:
                sys.exit()
        # out = out.strip()
        # if len(out)==0:
        #     pass
        # elif len(out)<maxLength:
        #     self.__msg ( " `- %s" % out )
        #     outurn
        # else:
        #     self.__msg ( " `- %s" % ( out[-maxLength:] ) )
        return err

    def clean ( self ):
        """ Deletes the output directory
        """
        self.__delete_dir(self.base_dir.get())

    def clean_all ( self ):
        """ Deletes all the directories that might have been made by CutLangWrapper
            Use with care.
        """

        if self.__confirmation("This will delete all directories created by running CutLangWrapper.\n"
                               "Proceed? (y/n)"):
            self.clean()
            self.__delete_dir("./CutLang")
            self.__delete_dir("./delphes")

    # =========================================================================
    # Private methods
    # =========================================================================

    def __confirmation(self, text):
        if self.auto_confirm == True:
            return True
        else:
            return False

    def __decompress(self, name, out_dir):
        basename = ".".join(os.path.basename(name).split(".")[:-1])
        out_name = os.path.join(out_dir, basename)
        self.__info(f"Decompressing {name} to {out_name} .")
        with open(out_name, 'wb') as f_out:
            in_f = gzip.open(name, 'rb')
            while True:
                s = in_f.read(self.GZIP_BLOCK)
                if s == b'':
                    break
                f_out.write(s)
            in_f.close()
        return out_name

    def __delete_dir ( self, f ):
        if os.path.exists ( f ):
            subprocess.getoutput ( "rm -rf %s" % f )

    def __get_bin_names(self, cutlangfile, name):
        bin_names = []
        with open(cutlangfile, "r") as f:
            lines = f.readlines()
            indices = [i for i, elem in enumerate(lines) if (not re.search(f"^region +{name}", elem) == None)]
            if len(indices) > 1:
                self.__error(f"Too many entries found for {name} in {cutlangfile}")
                return []
            if len(indices) < 1:
                self.__error(f"{name} not found in {cutlangfile}")
                return []
            print(f"indices : {indices}")
            lines = lines[indices[0] + 1:]
            print(lines[0])
            while  not len(lines) == 0 and re.search("^region", lines[0]) == None:
                if not re.search(" *bin", lines[0]) == None:
                    print("MATCH")
                    m = re.search(" +bin (?P<the_rest>.*)", lines[0])
                    bname = bname.split('#')[0]
                    bname = m.group("the_rest")
                    bname = bname.replace("[","").replace("[","")
                    # bname = bname.replace("<","lt").replace(">","mt")
                    bname = bname.replace("and","").replace("or","")
                    bname = bname.replace("AND","").replace("OR","")
                    bname = bname.replace("&&","").replace("||","")
                    bname = bname.replace("  "," ").replace(" ","_")
                    bin_names.append("_".join([name, bname]))
                lines.pop(0)
        # return bin_names
        return []

    def __get_embaked_name(self, analysis, topo):
        retval = ".".join([analysis.lower().replace("-","_"), topo, "embaked"])
        self.__info(f"Embaked file will be saved : {retval}.")
        return retval

    def __pick_delphes_card(self):
        if not re.search("ATLAS", self.analyses) == None:
            return os.path.abspath("./delphes/cards/delphes_card_ATLAS.tcl")
        elif not re.search("CMS", self.analyses) == None:
            return os.path.abspath("./delphes/cards/delphes_card_CMS.tcl")
        else:
            self.__error(f"Could not find a suitable Delphes card for analysis {self.analyses}. Exiting.")
            sys.exit()

    def __standardise_analysis(self, analysis):
        """Takes analysis name and returns it in format like: CMS-SUS-13-024"""
        analysis = analysis.replace("_", "-")
        analysis = analysis.upper()
        analysis = analysis.replace("SUSY", "SUS")
        return analysis

    def __info ( self, *msg ):
        """Print yellow info message"""
        print ( "%s[CutLangWrapper] %s%s" % ( colorama.Fore.YELLOW, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def __debug( self, *msg ):
        """Print green debug message."""
        print ( "%s[CutLangWrapper] %s%s" % ( colorama.Fore.GREEN, " ".join ( msg ), \
                   colorama.Fore.RESET ) )

    def __msg ( self, *msg):
        """Print normal message"""
        print ( "[CutLangWrapper] %s" % " ".join ( msg ) )

    def __error ( self, *msg ):
        """Print red error message"""
        print ( "%s[CutLangWrapper] Error: %s%s" % ( colorama.Fore.RED, " ".join ( msg ), \
                   colorama.Fore.RESET ) )




class Directory:
    def __init__(self, dirname, make = False):
        self.dirname = dirname
        if not os.path.exists(self.dirname):
            if make == True:
                os.makedirs(self.dirname)
            else:
                self.__error(f"Directory {self.dirname} does not exits. Aborting.")
                sys.exit()
        elif not os.path.isdir(self.dirname):
            self.__error(f"Directory {self.dirname} is not a directory. Aborting.")
            sys.exit()
    def get(self):
        return self.dirname

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='cutlang runner.')
    argparser.add_argument('-a', '--analyses', help='analyses, comma separated [cms_sus_16_033]',
                           type=str, default="cms_sus_16_033")
    argparser.add_argument('-d', '--hepmcfile', help='hepmcfile to be used as input for Delphes',
                           type=str, default="input.hepmc")
    argparser.add_argument('-j', '--njets', help='number of ISR jets [1]',
                           type=int, default=1)
    argparser.add_argument('-t', '--topo', help='topology [T2]',
                           type=str, default="T2")
    argparser.add_argument('-c', '--clean', help='clean all temporary files, then quit',
                           action="store_true")
    argparser.add_argument('-C', '--clean_all', help='clean all temporary files, even results directories, then quit',
                           action="store_true")
    mdefault = "Masses not specified"
    argparser.add_argument('-m', '--mass', help='mass range e.g."(100,110,10)"',
                           type=str, default=mdefault)
    argparser.add_argument('-p', '--nprocesses', help='number of process to run in parallel. 0 means 1 per CPU [1]',
                           type=int, default=1)
    argparser.add_argument('-r', '--rerun', help='force rerun, even if there is a summary file already',
                           action="store_true")
    args = argparser.parse_args()
    if args.clean:
        cutlang = CutLangWrapper(args.topo, args.njets, args.rerun, args.analyses)
        cutlang.clean()
        sys.exit()
    if args.clean_all:
        cutlang = CutLangWrapper(args.topo, args.njets, args.rerun, args.analyses)
        cutlang.clean_all()
        sys.exit()
    # if args.mass == "all":
    #     mass = bakeryHelpers.getListOfMasses(args.topo, args.njets)
    # else:
    #     mass = bakeryHelpers.parseMasses(args.mass)
    cutlang = CutLangWrapper(args.topo, args.njets, args.rerun, args.analyses)
    cutlang.run(args.mass, args.hepmcfile)
    # cutlang.__info( "%d points to produce, in %d processes" % (nm,nprocesses) )
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

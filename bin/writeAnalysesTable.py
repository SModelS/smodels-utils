#!/usr/bin/env python3
# vim: fileencoding=latin1

"""
.. module:: writeAnalysesTable
     :synopsis: generates a latex table with all analyses.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys, os, shutil
try:
    import subprocess as C ## python3
except:
    import commands as C ## python2
from smodels.base.physicsUnits import fb, TeV
from smodels.experiment.expResultObj import ExpResult
from smodels_utils.helper.various import hasLLHD
from smodels_utils.helper.prettyDescriptions import prettyTexAnalysisName
from smodels_utils.helper.databaseManipulations import filterSupersededFromList, filterFastLimFromList
from smodels_utils.helper.various import removeAnaIdSuffices
from smodels_utils.helper.bibtexTools import BibtexWriter
from typing import Union
import IPython

try:
    from ordered_set import OrderedSet
except Exception as e:
    print ( f"exception {e}" )
    print ( "please install ordered_set, e.g. via:" )
    if sys.version[0]=="3":
        print ( "pip3 install --user ordered_set" )
    else:
        print ( "pip install --user ordered_set" )
    sys.exit()

def isIn ( i, txnames ):
    """ is i in list txnames, leaving out onshell versions """
    for x in txnames:
        if i == x: return True
        if i == x+"(off)": return True
    return False


class Writer:
    def __init__ ( self, args ):
        """ writer class
        :param experiment: select on experiment, e.g. CMS, ATLAS, or both
        :param sqrts: select on sqrts (str)
        :param caption: write figure caption (bool)
        :param keep: keep latex files (bool)
        :param numbers: enumerate analysis (bool)
        :param description: add column for descriptions (bool)
        :param topos: add column for list of topologies (bool)
        :param showsqrts: show sqrts column (bool)
        :param longtable: longtable or tabular latex environment
        :param likelihoods: add likelihood information
        :param extended_likelihoods: add extended likelihood information
        :param bibtex: add bibtex references
        :param colors: use colors according to likelihood availability
        :param href: add href links

        .. code-block:: python3

        >>> writer = Writer( args )
        >>> writer.generateAnalysisTable( )
        >>> writer.createPngFile()
        """
        from smodels.experiment.databaseObj import Database
        self.args = vars ( args )
        self.database = Database ( args.database )
        self.ignorenonvalidated = args.ignorenonvalidated
        #Creat analyses list:
        self.bibtex = None
        self.timg = args.timg
        if args.bibtex:
            self.bibtex = BibtexWriter ( args.database )
        self.reference_results = None
        if args.reference_database != None:
            refdb = Database ( args.reference_database )
            ers = refdb.expResultList
            self.reference_db = refdb
            ids = set ( [ x.globalInfo.id for x in ers ] )
            self.reference_results = ids
        self.getExpResults ( superseded = args.superseded )
        self.texfile = args.output
        self.experiment = args.experiment
        self.likelihoods = args.likelihoods
        self.extended_likelihoods = args.extended_likelihoods
        self.addcombos = args.extended_likelihoods
        self.sqrts = args.sqrts.lower()
        self.colors = args.colors
        self.sqrts = self.sqrts.replace("*","").replace("tev","").replace("both","all").replace("none","all")
        if self.sqrts == "":
            self.sqrts = "all"
        if self.sqrts == "8":
            print ( "[writeAnalysesTable] sqrts is 8, so no column for combos" )
            self.addcombos = False
        self.keep = args.keep
        self.topos = args.topologies
        self.caption = args.caption
        self.numbers = args.enumerate
        self.prettyNames = args.prettyNames
        self.showsqrts = args.show_sqrts
        self.n_anas = 0 ## counter for analyses
        self.n_topos = 0 ## counter fo topologies
        self.lasts = None ## last sqrt-s (for hline )
        self.last_ana = None ## last ana id ( for counting )
        self.table = "tabular"
        if args.longtable:
            self.table = "longtable"

    def filterResults ( self, results : list, excludes : list ) -> list:
        """ given the list of excludes, filter results """
        import fnmatch
        ret = []
        for result in results:
            anaId = result.globalInfo.id
            isExcluded = False
            for exclude in excludes:
                if fnmatch.fnmatch ( anaId, exclude ):
                    if exclude == anaId:
                      print ( f"[plotBAM] dropping {anaId}" )
                    else:
                        print ( f"[plotBAM] dropping {anaId}: matches {exclude}" )
                    isExcluded = True
                    break
            if not isExcluded:
                ret.append ( result )
        return ret

    def getExpResults ( self, superseded ):
        """ get the experimental results, and filter
        :param superseded: allow superseded results
        """
        self.listOfAnalyses = []
        ers = self.database.getExpResults(
            useNonValidated = not self.ignorenonvalidated )
        ers = filterFastLimFromList ( ers )
        if superseded == False:
            ers = filterSupersededFromList ( ers )
        if self.args["minlumi"] > 0.:
            ers = self.filterLowLumiResults ( ers )
        if self.ignorenonvalidated:
            ers = self.filterNonValidated ( ers )
        self.listOfAnalyses = self.filterResults ( ers, self.args["exclude"].split(",") )

    def filterLowLumiResults ( self, expResults ):
        """ filter out results with a lumi below self.args['minlumi']
        """
        ret = []
        for er in expResults:
            lumi = er.globalInfo.lumi.asNumber(1/fb)
            if lumi > self.args['minlumi']:
                ret.append ( er )
        return ret

    def filterNonValidated ( self, expResults ):
        """ filter out results with a lumi below self.args['minlumi']
        """
        ret = []
        for er in expResults:
            hasValidated = False # check if at least one validated
            # result is in
            for ds in er.datasets:
                for txn in ds.txnameList:
                    if txn.validated == True:
                        hasValidated=True
                        break
            if hasValidated == True:
                ret.append ( er )
        return ret


    def sameAnaIds ( self, ana1, ana2 ):
        """ check if analysis ids are identical, *after* removing all
            the suffices """
        ana1n = removeAnaIdSuffices ( ana1.globalInfo.id )
        ana2n = removeAnaIdSuffices ( ana2.globalInfo.id )
        return ana1n == ana2n

    def addColor ( self, text ):
        if not self.colors:
            return text
        if self.colors:
            text="\\colorbox{"+self.currentcolor+"}{"+str(text)+"}"
        return text

    def getCombinationType ( self, ana : ExpResult,
           nextAna : ExpResult ) -> str:
        """ determine which type of SR combination we are dealing
            with """
        comb = " "
        for x in [ ana, nextAna ]:
            if x is None:
                continue
            if hasattr ( x.globalInfo, "jsonFiles" ):
                comb = "\\pyhf"
            #if nextIsSame and hasattr ( nextAna.globalInfo, "jsonFiles" ):
            #    comb = "JSON"
            if hasattr ( x.globalInfo, "covariance" ):
                comb = "SLv1"
            if hasattr ( x.datasets[0].dataInfo, "thirdMoment" ) and \
                    x.datasets[0].dataInfo.thirdMoment != None:
                comb = "SLv2"
            #if nextIsSame and hasattr ( nextAna.globalInfo, "covariance" ):
            #    comb = "Cov."
        return comb

    def getHepData ( self, ana : ExpResult ) -> str:
        """ obtain the hepdata for ana, currently unused """
        # FIXME for now we try with hepdata
        ret = ""
        for d in ana.datasets:
            for t in d.txnameList:
                if hasattr (t, "dataUrl" ) and t.dataUrl is not None:
                    url = t.dataUrl
                    if type(url)==list:
                        url = ",".join ( url )
                    if "doi.org" in url and "hepdata" in url:
                        if "/t" in url:
                            p = url.find ( "/t" )
                            url = url[:p]
                        print ( "good:", url )
                        ret = url
                        return ret
                    if "doi.org" in url:
                        return url
                    print ( "what do i do with", url )
        return ret

    def hasChanged ( self, ana : ExpResult, nextAna : None|ExpResult,
                     reportOnlyNew : bool = False ) -> bool:
        """ has the analysis changed with respect to the reference database?
        :param reportOnlyNew: if true, then only entirely new results count
        """
        hasChanged = False
        if self.reference_results is not None:
            if ana.globalInfo.id not in self.reference_results:
                hasChanged = True
            lastUpdate = ana.globalInfo.lastUpdate
            from datetime import datetime
            dateformat = "%Y/%M/%d"
            lastUpdate = datetime.strptime ( lastUpdate, dateformat )
            if not reportOnlyNew:
                dTs = { "upperLimit", "efficiencyMap" }
                dTs = set()
                for dt in ana.datasets:
                    dTs.add ( dt.getType() )
                if nextAna is not None:
                    for dt in nextAna.datasets:
                        dTs.add ( dt.getType() )
                dTs = list ( dTs )
                refanas = self.reference_db.getExpResults ( [ ana.globalInfo.id+x for x in  [ "", "-agg", "-ma5", "-adl", "-eff" ] ] )
                refdTs = set()
                for refana in refanas:
                    for dt in refana.datasets:
                        refdTs.add ( dt.getType() )
                if len(refdTs) < len(dTs):
                    hasChanged = True
                if len(refanas)==0:
                    hasChanged = True
                else:
                    refana = refanas[0]
                    refLastUpdate = refana.globalInfo.lastUpdate
                    refLastUpdate = datetime.strptime ( refLastUpdate, dateformat )
                    if refLastUpdate < lastUpdate:
                        hasChanged = True
        if False:
            print ( )
            print ( f"has {ana.globalInfo.id} changed? {hasChanged}" )
            print ( f"refanas {refanas}" )
            print ( f"dTs {dTs} refdTs {refdTs}" )
        return hasChanged

    def writeSingleAna ( self, ana : ExpResult, nextIsSame : bool,
            nextAna : Union[None,ExpResult] = None ):
        """ write the entry of a single analysis
        :param nextIsSame: true, if next is same
        :param nextAna: the next analysis (if same)
        """
        lines= [ "" ]
        hasChanged = self.hasChanged ( ana, nextAna, reportOnlyNew=False )
        sqrts = int ( ana.globalInfo.sqrts.asNumber(TeV) )
        if sqrts != self.lasts and self.lasts != None:
            lines[0] = "\\hline\n"
        ananr=""
        anaid = removeAnaIdSuffices ( ana.globalInfo.id )
        if anaid != self.last_ana:
            self.n_anas += 1
            self.last_ana = anaid
            ananr="%d" % self.n_anas
        ret = ""
        txnobjs = ana.getTxNames()
        t_txnames = [ x.txName for x in txnobjs ]
        t_txnames.sort()
        txnames=[]
        for i in OrderedSet ( t_txnames ):
            if "off" in i:
                on = i.replace("off","")
                if on in txnames: txnames.remove ( on )
                txnames.append ( i.replace("off","[off]" ) )
            else:
                if not isIn ( i, txnames ):
                    txnames.append ( i )
        alltxes = f"{len(txnames)}: "
        maxn = 40
        if self.prettyNames:
            maxn=15
        first=True
        for i in txnames:
            if not first:
                alltxes+=", "
            first=False
            alltxes+= f"{i}"
            if len(alltxes)>maxn:
                alltxes+="..."
                break

        prettyName = ana.globalInfo.prettyName
        dataType = ana.datasets[0].dataInfo.dataType
        if nextIsSame and type(nextAna) != type(None):
            pname2 = nextAna.globalInfo.prettyName
            ## if we have two and the second is the EM, we go with that
            if dataType == "upperLimit":
                prettyName = pname2
        dt = "eff" if dataType == "efficiencyMap" else "ul"
        self.currentcolor = "white" #  "red!65"
        llhds = "no"
        if hasLLHD ( ana ):
            llhds = "yes"
        if nextIsSame:
            llhds = "yes"
            dt = "ul, eff"
        if "ul" in dt:
            if hasLLHD ( ana ):
                self.currentcolor = "red!65"
                # self.currentcolor = "orange!65"
        if nextIsSame or "eff" in dt:
            self.currentcolor = "orange!65"
            # self.currentcolor = "yellow!75"
        hasComb = False
        darkgreen = "darkgreen!85"
        if hasattr ( ana.globalInfo, "jsonFiles" ):
            hasComb = True
            self.currentcolor = darkgreen
        if nextIsSame and hasattr ( nextAna.globalInfo, "jsonFiles" ):
            hasComb = True
            self.currentcolor = darkgreen
        lightgreen = "green!60"
        yellow = "yellow!75"
        if hasattr ( ana.globalInfo, "covariance" ):
            hasComb = True
            self.currentcolor = yellow
            # self.currentcolor = lightgreen
        if nextIsSame and hasattr ( nextAna.globalInfo, "covariance" ):
            hasComb = True
            self.currentcolor = yellow
            # self.currentcolor = lightgreen
        #if hasComb:
        #    self.currentcolor = "green"
        # ref = "\\href{%s}{[%d]}" % ( ana.globalInfo.url, nr )
        gi_id = ana.globalInfo.id.replace("/data-cut","").replace("-eff","").replace("/","")
        gi_id = removeAnaIdSuffices ( gi_id )
        Url = ana.globalInfo.url
        if " " in Url: Url = Url[:Url.find(" ")]
        #if "ATLAS-CONF-2013-093" in Url:
            # alltxes="xxx"
        #    Url="http://www.google.com"
        #    gi_id="vvv"
        if self.args["href"]:
            Id = "\\href{%s}{%s}" % ( Url, gi_id )
        else:
            Id = gi_id
        Id = self.addColor ( Id )
        if self.bibtex != None:
            citeme = self.bibtex.query ( gi_id )
            if citeme.startswith ( "no entry" ):
                citme = "FIXME"
            Id += rf"~\cite{{{citeme}}}"
        if self.numbers:
            lines[0]+=f"{self.addColor(ananr)} &"
        lines[0] += f"{Id} & "
        if self.prettyNames:
            pn = prettyTexAnalysisName ( prettyName )
            # pn = self.addColor ( pn )
            lines[0] += f"{pn} &"
        if self.topos:
            lines[0] += f"{alltxes} &"
        if not self.extended_likelihoods:
            lines[0] += f"{dt} &"
        lumi = ana.globalInfo.lumi.asNumber(1/fb)
        # lumi = self.addColor ( lumi )
        lines[0] += f" {lumi} "
        if self.showsqrts:
            lines[0] += f"& {self.addColor ( sqrts )}"
        if self.likelihoods:
            lines[0] += f"& {llhds} "
        if self.extended_likelihoods:
            ulobs, ulexp, em = " ", " ", " "
            check = "\\checkmark" ## check="x"
            if "ul" in dt:
                ulobs = check
                if hasLLHD ( ana ):
                    ulexp = check
            if "eff" in dt:
                em = check
            #ulobs, ulexp, em, comb = "x", "x", "x", "JSON"
            lines[0] += f"& {ulobs} & {ulexp} & {em}"
        if self.addcombos:
            comb = self.getCombinationType ( ana, nextAna )
            lines[0] += f"& {comb}"
        if hasChanged:
            for i,line in enumerate(lines):
                lines[i] = "\\bf{" + line+"}"
        lines[0] += " \\\\\n"
        self.lasts = sqrts
        self.n_topos += len(txnames)
        return "\\n".join ( lines ), len(txnames)

    def sqrtsIsMet ( self, sqrts ):
        """ the sqrts criterion is met, either because it is "all", or because
            the center of mass energy is correct """
        if self.sqrts == "all":
            return True
        if abs(int(self.sqrts)-sqrts.asNumber(TeV))<1e-5:
            return True
        return False

    def experimentIsMet ( self, anaid ):
        if self.experiment in [ "both", "all" ]:
            return True
        if self.experiment in anaid:
            return True
        return False

    def generateAnalysisTable( self ):
        """ Generates a raw latex table with all the analyses in listOfAnalyses,
        writes it to texfile (if not None), and returns it as its return value.
        :param texfile: where the tex gets written to, e.g. tab.tex
        """
        frmt = "|l"
        if self.numbers:
            frmt = "|r" + frmt
        if not self.extended_likelihoods:
            frmt += "|l"
        if self.prettyNames:
            frmt += "|l"
        frmt += "|c|c|c|"
        if self.likelihoods:
            frmt = frmt + "r|"
        if self.extended_likelihoods:
            frmt = frmt + "c|c|c|c|"
        toprint = rf"\begin{{{self.table}}}{{{frmt}}}"
        toprint += "\n"
        toprint += r"\hline"
        if self.numbers:
            toprint += r"{\bf \#} &"
        toprint += "{\\bf ID} & "
        if self.prettyNames:
            # toprint += "{\\bf Pretty Name} & "
            toprint += "{\\bf Short Description} & "

        if self.topos:
            toprint += "{\\bf Topologies} &"
        if not self.extended_likelihoods:
            toprint += "{\\bf Type} & "
        toprint += "{\\bf $\\mathcal{L}$ [fb$^{-1}$] } "
        if self.showsqrts:
            toprint += "& {\\bf $\\sqrt s$ } "
        if self.likelihoods:
            toprint += "& {\\bf likelihoods}"
        if self.extended_likelihoods:
            toprint += r"& {\bf UL$_\mathrm{obs}$} & {\bf UL$_\mathrm{exp}$} & {\bf EM}"
        if self.addcombos:
            toprint += "& {\\bf comb.}"
        toprint += r"\\"
        toprint += "\n"
        toprint += r"\hline"
        toprint += "\n"
        nextIsSame = False ## in case the next is the same, just "eff" not "ul"
        for ctr,ana in enumerate(self.listOfAnalyses):
            if nextIsSame:
                ## skip! but first check if the next to next is also the same
                nextIsSame = False
                if ctr+1 < len(self.listOfAnalyses):
                    if self.sameAnaIds ( self.listOfAnalyses[ctr+1], ana ):
                        nextIsSame = True
                continue
            if ctr+1 < len(self.listOfAnalyses):
                # if self.listOfAnalyses[ctr+1].globalInfo.id == ana.globalInfo.id:
                if self.sameAnaIds ( self.listOfAnalyses[ctr+1], ana ):
                    nextIsSame = True
            if self.experimentIsMet ( ana.globalInfo.id ):
                if self.sqrtsIsMet ( ana.globalInfo.sqrts ):
                    nextAna = None
                    if nextIsSame:
                        nextAna = self.listOfAnalyses[ctr+1]
                    tp, n_topos = self.writeSingleAna ( ana, nextIsSame, nextAna )
                    toprint += tp
        toprint += "\\hline\n"
        if self.caption:
            caption = "\\caption{SModelS database"
            if self.experiment != "both": caption += f" ({self.experiment})"
            toprint += "%s}\n" % caption
            toprint += "\\label{tab:SModelS database}\n"
        toprint += "\\end{%s}\n" % self.table

        if self.texfile:
            outfile = open(self.texfile,"w")
            outfile.write(toprint)
            outfile.close()

        self.createLatexDocument ( self.texfile )
        self.pprint ( "number of analyses:",self.n_anas )
        self.pprint ( "number of topo/ana pairs:",self.n_topos )
        return toprint

    def pprint ( self, *args ):
        print ( "[writeAnalysesTable]",*args )

    def createPdfFile ( self ):
        texfile = "tab.tex"
        base = "smodels"
        if self.experiment != "both":
            base = self.experiment
        if self.sqrts != "all":
            base += str(self.sqrts)
        self.pprint ( f"now latexing smodels.tex (which includes {self.texfile})" )
        o1 = C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        o2 = C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        o3 = C.getoutput ( "bibtex smodels" )
        o4 = C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        o5 = C.getoutput ( "bibtex smodels" )
        o6 = C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        #if os.path.isfile("smodels.dvi"):
        #    C.getoutput( "dvipdf smodels.dvi" )
        self.pprint ( f"done latexing, see {base}.pdf" )
        if os.path.exists ( "/bin/pdftrimwhite" ):
            trimcmd = f"pdftrimwhite {base}.pdf {base}trimmed.pdf"
            C.getoutput ( trimcmd )
            self.pprint ( f"trimmed version: {base}trimmed.pdf" )
        if self.experiment != "both":
            C.getoutput ( f"mv smodels.pdf {base}.pdf" )
            # C.getoutput ( "mv smodels.ps %s.ps" % experiment )
        for i in [ "smodels.log", "smodels.out", "smodels.aux" ]:
            if os.path.exists ( i ):
                os.unlink ( i )
        if not self.keep:
            for i in [ "smodels.tex", "tab.tex" ]:
                os.unlink ( i )

    def createLatexDocument ( self, texfile ):
        repl="@@@TEXFILE@@@"
        bibtexrepl = "@@@BIBTEXSTUFF@@@"
        bibtexstuff = ""
        if self.bibtex != None:
            bibtexfile = f"{args.database}/database.bib"
            if not os.path.exists ( bibtexfile ):
                print ( f"[writeAnalysesTable] cannot find bibtexfile {bibtexfile}. skip bibtex." )
            else:
                cmd = "cp {bibtexfile} ."
                C.getoutput ( cmd )
                bibtexstuff = r"\\renewcommand{\\text}{\\mathrm};\\newpage;\\bibliography{database};\\bibliographystyle{unsrt}"
                if False:
                    ## lets comment out the bibliography
                    bibtexstuff = bibtexstuff.replace(";",";%" )
        path = os.path.dirname ( os.path.abspath ( __file__ ) )
        path = path.replace("/bin","/share")
        cmd= f"cat {path}/AnalysesListTemplate.tex | sed -e 's/{repl}/{texfile}/' | sed -e 's/{bibtexrepl}/{bibtexstuff}/' | tr ';' '\n' > smodels.tex"
        o = C.getoutput ( cmd )

    def createPngFile ( self ):
        base = "smodels"
        if self.experiment != "both":
            base = self.experiment
        if self.sqrts != "all":
            base += str(self.sqrts)
        pngfile= base + ".png"
        pdffile= base + ".pdf"
        self.pprint ( f"now creating {base}.png" )
        whiteBG = True
        swbg=""
        if whiteBG:
            swbg="-alpha off"
        cmd = f"rm {pngfile.replace('.png','*.png')}"
        C.getoutput ( cmd )
        cmd = f"/usr/bin/convert {swbg} -antialias -density 600 -trim {pdffile} {pngfile}"
        print ( f"[writeAnalysesTable] {cmd}" )
        o = C.getoutput ( cmd )
        if len(o)>0:
            print ( o )
        if self.timg:
            a = shutil.which ( "timg" )
            if a:
                cmd = f"timg -p kitty {pngfile.replace('.png','*.png')}"
                # print ( cmd )
                a = C.getoutput ( cmd )
                print ( a )

if __name__ == "__main__":
        import setPath, argparse, types, os

        argparser = argparse.ArgumentParser(description=
                      'simple tool to generate a latex table with all analyses used')
        dbpath = os.path.abspath( '../../smodels-database/' )
        argparser.add_argument ( '-d', '--database', nargs='?',
            help=f'path to database [{dbpath}]', type=str,
            default=dbpath )
        argparser.add_argument ( '-r', '--reference_database',
            nargs='?', help=f'path to reference database, if given make new entries bold [None]',
            type=str, default=None )
        argparser.add_argument ( '--minlumi', help="consider results only above a certain luminosity, in 1/fb [0.]",
            type=float, default=0. )
        outfile = "tab.tex"
        argparser.add_argument ( '-o', '--output', nargs='?',
            help=f'output file [{outfile}]', type=str,
            default=outfile )
        argparser.add_argument('-k', '--keep',
            help='keep tex files', action='store_true' )
        argparser.add_argument ( '-e', '--experiment', nargs='?',
            help='experiment [both]', type=str, default='both')
        argparser.add_argument ( '-S', '--sqrts', nargs='?',
            help="show only certain runs, e.g. 8, 13, or 'all' ['all']",
            type=str, default='all' )
        argparser.add_argument('-p', '--pdf', help='produce pdf file',
            action='store_true' )
        argparser.add_argument('-P', '--png', help='produce png file',
            action='store_true' )
        argparser.add_argument('-s', '--superseded', help='add superseded results',
            action='store_true' )
        argparser.add_argument('-c', '--caption', help='add figure caption',
            action='store_true' )
        argparser.add_argument('-n', '--enumerate', help='enumerate analyses',
            action='store_true' )
        argparser.add_argument('-L', '--likelihoods', help='add likelihood info',
            action='store_true' )
        argparser.add_argument('-X', '--extended_likelihoods',
            help='add extended likelihood info', action='store_true' )
        argparser.add_argument('-t', '--topologies', help='add topologies',
            action='store_true' )
        argparser.add_argument('-l', '--longtable', help='use longtable not tabular',
            action='store_true' )
        argparser.add_argument('--show_sqrts', help='show sqrts column',
            action='store_true' )
        argparser.add_argument('--timg', '-T', help='run timg on picture',
            action='store_true' )
        argparser.add_argument('--ignorenonvalidated',
            help='ignore non-validated results',
            action='store_true' )
        argparser.add_argument('-N', '--prettyNames',
            help='add column for description of analyses', action='store_true' )
        argparser.add_argument('-b', '--bibtex', help='add bibtex references',
            action='store_true' )
        argparser.add_argument('--colors',
            help='use colors according to availability of likelihood',
            action='store_true' )
        argparser.add_argument( '-H','--href', help='add href links',
            action='store_true' )
        argparser.add_argument( '--combinations', help='cycle through all combinations (8TeV/13TeV, CMS/ATLAS)',
            action='store_true' )
        argparser.add_argument ( '--exclude',
            help='exclude this comma-separated list of analyses, wildcards allowed [none]',
            type=str, default='' )
        args=argparser.parse_args()
        if not args.combinations:
            writer = Writer ( args )
            #Generate table:
            writer.generateAnalysisTable( )
            # create pdf
            if args.pdf or args.png:
                writer.createPdfFile()
            if args.png:
                writer.createPngFile()
            sys.exit()
        ## asked for --combinations
        writer = Writer ( args )
        for s in [ 8, 13 ]:
            writer.sqrts = str(s)
            for e in [ "CMS", "ATLAS" ]:
                writer.experiment = e
                #Generate table:
                writer.generateAnalysisTable( )
                # create pdf
                if args.pdf or args.png:
                    writer.createPdfFile()
                if args.png:
                    writer.createPngFile()
                if args.keep:
                    cmd = f"cp tab.tex {e}{s}.tex"
                    C.getoutput ( cmd )

#!/usr/bin/env python3
# vim: fileencoding=latin1

## todo in pretty names: ETmiss vs Etmiss vs MET. 0 or >=1 leptons? WTF?
## same-sign versus same sign versus SS FIXME

"""
.. module:: analysesTable
     :synopsis: generates a latex table with all analyses.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function
import sys
try:
    import subprocess as C ## python3
except:
    import commands as C ## python2
from smodels.tools.physicsUnits import fb, TeV
import IPython

try:
    from ordered_set import OrderedSet
except Exception as e:
    print ( "exception",e )
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
    def __init__ ( self, db, experiment, keep, caption, numbers, prettyNames,
                         superseded ):
        """ writer class
        :param caption: write figure caption (bool)
        :param keep: keep latex files (bool)
        :param numbers: enumerate analysis (bool)
        :param description: add column for descriptions (bool)
        """
        from smodels.experiment.databaseObj import Database
        database = Database ( args.database )
        #Creat analyses list:
        self.listOfAnalyses = database.getExpResults( useSuperseded=superseded )
        self.experiment = experiment 
        self.keep = keep
        self.caption = caption
        self.numbers = numbers
        self.prettyNames = prettyNames
        self.n_anas = 0 ## counter for analyses
        self.n_topos = 0 ## counter fo topologies
        self.lasts = None ## last sqrt-s (for hline )
        self.last_ana = None ## last ana id ( for counting )

    def writeSingleAna ( self, ana ):
        """ write the entry of a single analysis """
        lines= [ "" ]
        sqrts = int ( ana.globalInfo.sqrts.asNumber(TeV) ) 
        if sqrts != self.lasts and self.lasts != None:
            lines[0] = "\\hline\n"
        ananr=""
        anaid = ana.globalInfo.id
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
        alltxes = "%d: " % len(txnames)
        maxn = 40
        if self.prettyNames:
            maxn=15
        first=True
        for i in txnames:
            if not first:
                alltxes+=", "
            first=False
            alltxes+= "%s" % i
            if len(alltxes)>maxn:
                alltxes+="..."
                break

        prettyName = ana.globalInfo.prettyName
        dataType = ana.datasets[0].dataInfo.dataType
        dt = "eff" if dataType == "efficiencyMap" else "ul"
        # ref = "\\href{%s}{[%d]}" % ( ana.globalInfo.url, nr )
        gi_id = ana.globalInfo.id.replace("/data-cut","").replace("-eff","").replace("/","")
        Url = ana.globalInfo.url
        if " " in Url: Url = Url[:Url.find(" ")]
        #if "ATLAS-CONF-2013-093" in Url:
            # alltxes="xxx"
        #    Url="http://www.google.com"
        #    gi_id="vvv"
        Id = "\\href{%s}{%s}" % ( Url, gi_id )
        if self.numbers:
            lines[0]+="%s &" % ananr
        lines[0] += "%s & " % Id
        if self.prettyNames:
            pn = prettyName.replace(">","$>$").replace("<","$<$")
            pn = pn.replace("0 or $>$=1 leptons +","" )
            pn = pn.replace("photon photon","$\gamma\gamma$" )
            pn = pn.replace("SF OS","SFOS" )
            pn = pn.replace("jet multiplicity","n$_{jets}$" )
            pn = pn.replace("Higgs","H" )
            pn = pn.replace("searches in","to" )
            pn = pn.replace("same-sign","SS" )
            pn = pn.replace("Multilepton","multi-l" )
            pn = pn.replace("multilepton","multi-l" )
            pn = pn.replace("leptons","l's" )
            pn = pn.replace("lepton","l" )
            pn = pn.replace("dilepton","di\-l" )
            pn = pn.replace("productions with decays to","prod, to ")
            pn = pn.replace("photon","$\gamma$" )
            pn = pn.replace("Photon","$\gamma$" )
            pn = pn.replace("-$>$","$\\rightarrow$" )
            pn = pn.replace("final states","")
            pn = pn.replace("final state","")
            pn = pn.replace("ETmiss","$\\not{\!\!E}_T$")
            pn = pn.replace("Etmiss","$\\not{\!\!E}_T$")
            pn = pn.replace("MET","$\\not{\!\!E}_T$")
            pn = pn.replace("M_CT","M$_CT$" )
            pn = pn.replace("alpha_T","$\\alpha_T$" )
            if pn[-1]==")":
                pos = pn.rfind ( "(" )
                pn = pn[:pos]
            # pn = prettyName[:30]
            lines[0] += "%s &" % pn
        lines[0] += "%s & %s & %s & %s \\\\\n" % \
                     ( alltxes, dt, ana.globalInfo.lumi.asNumber(1/fb), 
                       sqrts )
        self.lasts = sqrts
        self.n_topos += len(txnames)
        return "\\n".join ( lines ), len(txnames)

    def generateAnalysisTable(self ):
        """ Generates a raw latex table with all the analyses in listOfAnalyses,
        writes it to texfile (if not None), and returns it as its return value. """
        texfile = "tab.tex"
        frmt = "|l|l|c|c|c|"
        if self.prettyNames:
            frmt = "|l|l|l|c|c|c|"
        if self.numbers:
            frmt = "|r" + frmt
        toprint = "\\begin{longtable}{%s}\n\hline\n" % frmt
        if self.numbers:
            toprint +="{\\bf \#} &"
        toprint += "{\\bf ID} & "
        if self.prettyNames:
            toprint += "{\\bf Pretty Name} & "
            

        toprint += "{\\bf Topologies} & {\\bf Type} & {\\bf $\\mathcal{L}$ [fb$^{-1}$] } & {\\bf $\\sqrt s$ }"
        toprint += "\\\\\n\hline\n"
        for ana in self.listOfAnalyses:
            if self.experiment == "both" or self.experiment in ana.globalInfo.id:
                tp, n_topos = self.writeSingleAna ( ana )
                toprint += tp
        toprint += "\\hline\n"
        if self.caption:
            caption = "\\caption{SModelS database"
            if self.experiment != "both": caption += " (%s)" % self.experiment
            toprint += "%s}\n" % caption
            toprint += "\\label{tab:SModelS database}\n"
        toprint += "\\end{longtable}\n"

        if texfile:
            outfile = open(texfile,"w")
            outfile.write(toprint)
            outfile.close()

        self.createLatexDocument ( texfile )
        print ( "Number of analyses",self.n_anas )
        print ( "Number of topos",self.n_topos )
        return toprint

    def createPdfFile ( self ):
        texfile = "tab.tex"
        base = "smodels"
        if self.experiment != "both":
            base = self.experiment
        print ( "now latexing smodels.tex" )
        C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        #if os.path.isfile("smodels.dvi"):
        #    C.getoutput( "dvipdf smodels.dvi" )
        print ( "done latexing, see %s.pdf" % base )
        if self.experiment != "both":
            C.getoutput ( "mv smodels.pdf %s.pdf" % base )
            # C.getoutput ( "mv smodels.ps %s.ps" % experiment )
        for i in [ "smodels.log", "smodels.out", "smodels.aux" ]:
            os.unlink ( i ) 
        if not self.keep:
            for i in [ "smodels.tex", "tab.tex" ]:
                os.unlink ( i )

    def createLatexDocument ( self, texfile ):
        repl="@@@TEXFILE@@@"
        cmd="cat ../share/AnalysesListTemplate.tex | sed -e 's/%s/%s/' > smodels.tex" % ( repl, texfile )
        C.getoutput ( cmd )


    def createPngFile ( self ):
        base = "smodels"
        if self.experiment != "both":
            base = self.experiment
        pngfile= base + ".png"
        pdffile= base + ".pdf"
        print ( "now creating %s-X.png" % base )
        cmd = "convert -trim %s %s" % ( pdffile, pngfile )
        o = C.getoutput ( cmd )
        if len(o)>0:
            print ( o )

if __name__ == "__main__":
        import setPath, argparse, types, os

        argparser = argparse.ArgumentParser(description=
                      'simple tool to generate a latex table with all analysis used')
        dbpath = os.path.abspath( '../../smodels-database/' )
        argparser.add_argument ( '-d', '--database', nargs='?', 
                            help='path to database [%s]' % dbpath, type=str, 
                            default=dbpath )
        argparser.add_argument('-k', '--keep', help='keep tex files', 
                            action='store_true' )
        argparser.add_argument ( '-e', '--experiment', nargs='?', 
                            help='experiment [both]', type=str, default='both')
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
        argparser.add_argument('-N', '--prettyNames', 
                            help='add column for description of analyses', 
                            action='store_true' )
        args=argparser.parse_args()
        writer = Writer( db = args.database, experiment=args.experiment,
                         keep = args.keep, caption = args.caption,
                         numbers = args.enumerate, prettyNames=args.prettyNames,
                         superseded = args.superseded )
        #Generate table:
        writer.generateAnalysisTable()
        # create pdf
        if args.pdf or args.png: 
            writer.createPdfFile()
        if args.png:
            writer.createPngFile()

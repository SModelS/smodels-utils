#!/usr/bin/env python3
# vim: fileencoding=latin1

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
    def __init__ ( self, experiment ):
        self.experiment = experiment 

    def writeSingleAna ( self, ana ):
        """ write the entry of a single analysis """
        #IPython.embed()
        #sys.exit()
        ret = ""
        lines= [ "" ]
        # print ana.globalInfo.id
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
        first=True
        for i in txnames:
            if not first:
                alltxes+=", "
            first=False
            alltxes+= "%s" % i
            if len(alltxes)>25: # 40
                alltxes+="..."
                break

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
        lines[0] += "%s & %s & %s & %s & %s \\\\\n" % \
                     ( Id, alltxes, dt, ana.globalInfo.lumi.asNumber(1/fb), 
                       int ( ana.globalInfo.sqrts.asNumber(TeV) ) )
        return "\\n".join ( lines ), len(txnames)

    def generateAnalysisTable(self, listOfAnalyses ):
        """ Generates a raw latex table with all the analyses in listOfAnalyses,
        writes it to texfile (if not None), and returns it as its return value. """
        texfile = "tab.tex"
        toprint = "\\begin{longtable}{|l|l|c|c|c|}\n\hline\n"

        toprint += "{\\bf ID} & {\\bf Topologies} & {\\bf Type} & {\\bf $\\mathcal{L}$ [fb$^{-1}$] } & {\\bf $\\sqrt s$ }"
        toprint += "\\\\\n\hline\n"
        num_analyses = 0
        num_topos = 0
        for ana in listOfAnalyses:
            if self.experiment == "both" or self.experiment in ana.globalInfo.id:
                tp, n_topos = self.writeSingleAna ( ana )
                toprint += tp
                num_topos += n_topos
                num_analyses += 1
        toprint += "\\hline\n"
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
        print ( "Number of analyses",num_analyses )
        print ( "Number of topos",num_topos )
        return toprint

    def createPdfFile ( self, no_unlink ):
        texfile = "tab.tex"
        base = "smodels"
        if self.experiment != "both":
            base = self.experiment
        print ( "now latexing smodels.tex" )
        C.getoutput ( "latex -interaction=nonstopmode smodels.tex" )
        #if os.path.isfile("smodels.dvi"):
        #    C.getoutput( "dvipdf smodels.dvi" )
        print ( "done latexing, see %s.pdf" % base )
        if self.experiment != "both":
            C.getoutput ( "mv smodels.pdf %s.pdf" % base )
            # C.getoutput ( "mv smodels.ps %s.ps" % experiment )
        for i in [ "smodels.log", "smodels.out", "smodels.aux" ]:
            os.unlink ( i ) 
        if not no_unlink:
            for i in [ "smodels.tex", "tab.tex" ]:
                os.unlink ( i )

    def createLatexDocument ( self, texfile ):
        repl="@@@TEXFILE@@@"
        cmd="cat ../share/AnalysesListTemplate.tex | sed -e 's/%s/%s/' > smodels.tex" % ( repl, texfile )
        C.getoutput ( cmd )


    def createPngFile ( self, no_unlink ):
        base = "smodels"
        if self.experiment != "both":
            base = self.experiment
        pngfile= base + ".png"
        pdffile= base + ".pdf"
        print ( "now creating %s-X.png" % base )
        cmd = "convert %s %s" % ( pdffile, pngfile )
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
        argparser.add_argument('-n', '--no_unlink', help='do not remove tex file', 
                            action='store_true' )
        argparser.add_argument ( '-e', '--experiment', nargs='?', 
                            help='experiment [both]', type=str, default='both')
        argparser.add_argument('-p', '--pdf', help='produce pdf file', 
                            action='store_true' )
        argparser.add_argument('-P', '--png', help='produce png file', 
                            action='store_true' )
        args=argparser.parse_args()
        from smodels.experiment.databaseObj import Database
        database = Database ( args.database )
        #Creat analyses list:
        listOfAnalyses = database.getExpResults()
        writer = Writer( experiment=args.experiment )
        #Generate table:
        writer.generateAnalysisTable( listOfAnalyses )
        # create pdf
        if args.pdf or args.png: 
            writer.createPdfFile ( args.no_unlink )
        if args.png:
            writer.createPngFile ( args.no_unlink )

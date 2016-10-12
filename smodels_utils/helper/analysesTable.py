#!/usr/bin/env python

# vim: fileencoding=latin1

"""
.. module:: analysesTable
     :synopsis: generates a latex table with all analyses.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import sys
import commands
from smodels.tools.physicsUnits import fb, TeV
import IPython

try:
    from ordered_set import OrderedSet
except ExceptionError,e:
    print "exception",e
    print "please install ordered_set, e.g. via:"
    print "pip install --user ordered_set"
    sys.exit()

def isIn ( i, txnames ):
    """ is i in list txnames, leaving out onshell versions """
    for x in txnames:
        if i == x: return True
        if i == x+"(off)": return True
    return False

def writeSingleAna ( ana ):
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
        if len(alltxes)>30:
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

def generateAnalysisTable(listOfAnalyses, texfile=None, experiment = "both" ):
    """ Generates a raw latex table with all the analyses in listOfAnalyses,
    writes it to texfile (if not None), and returns it as its return value. """

    toprint = """
\\begin{longtable}{|l|l|c|c|c|}
\hline
{\\bf ID} & {\\bf Topologies} & {\\bf Type} & {\\bf $\\mathcal{L}$ [fb$^{-1}$] } & {\\bf $\\sqrt s$ } \\\\
\hline
"""
    num_analyses = 0
    num_topos = 0
    for ana in listOfAnalyses:
        if experiment == "both" or experiment in ana.globalInfo.id:
            tp, n_topos = writeSingleAna ( ana )
            toprint += tp
            num_topos += n_topos
            num_analyses += 1
    toprint += "\\hline\n"
    caption = "\\caption{SModelS database"
    if experiment != "both": caption += " (%s)" % experiment
    toprint += "%s}\n" % caption
    toprint += "\\label{tab:SModelS database}\n"
    toprint += "\\end{longtable}\n"

    if texfile:
        outfile = open(texfile,"w")
        outfile.write(toprint)
        outfile.close()

    createLatexDocument ( texfile )
    print "Number of analyses",num_analyses
    print "Number of topos",num_topos
    return toprint


def createLatexDocument ( texfile ):
    repl="@@@TEXFILE@@@"
    cmd="cat template.tex | sed -e 's/%s/%s/' > /tmp/smodels.tex" % ( repl, texfile )
    commands.getoutput ( cmd )

def createPdfFile ( texfile, no_unlink, experiment ):
    pdffile=texfile.replace(".tex",".pdf" )
    #repl="@@@TEXFILE@@@"
    #cmd="cat template.tex | sed -e 's/%s/%s/' > /tmp/smodels.tex" % ( repl, texfile )
    #commands.getoutput ( cmd )
    print "now latexing"
    commands.getoutput ( "latex -interaction=nonstopmode /tmp/smodels.tex" )
    if os.path.isfile("smodels.dvi"):
        commands.getoutput( "dvips smodels.dvi" )
    print "done latexing"
    if experiment != "both":
        commands.getoutput ( "cp smodels.pdf %s.pdf" % experiment )
        commands.getoutput ( "cp smodels.ps %s.ps" % experiment )
    os.unlink ( "smodels.log" )
    os.unlink ( "smodels.aux" )
    if not no_unlink:
        os.unlink ( "/tmp/smodels.tex" )

if __name__ == "__main__":
        import setPath, argparse, types, os

        argparser = argparse.ArgumentParser(description=
                      'simple tool to generate a latex table with all analysis used')
        dbpath = os.path.abspath( '../../../smodels-database/' )
        argparser.add_argument ( '-d', '--database', nargs='?', 
                            help='path to database', 
                            type=types.StringType, default=dbpath )
        argparser.add_argument ( '-o', '--output', nargs='?', help='output file', 
                            type=types.StringType, default='tab.tex')
        argparser.add_argument('-n', '--no_unlink', help='do not remove tex file', 
                            action='store_true' )
        argparser.add_argument ( '-e', '--experiment', nargs='?', help='experiment', 
                            type=types.StringType, default='both')
        argparser.add_argument('-p', '--pdf', help='produce pdf file', 
                            action='store_true' )
        args=argparser.parse_args()
        from smodels.experiment.databaseObj import Database
        database = Database ( args.database )
        #Creat analyses list:
        listOfAnalyses = database.getExpResults()
        #Generate table:
        generateAnalysisTable( listOfAnalyses, texfile=args.output, experiment=args.experiment )
        # create pdf
        if args.pdf: createPdfFile ( args.output, args.no_unlink, args.experiment )

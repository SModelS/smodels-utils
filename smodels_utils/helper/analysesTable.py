#!/usr/bin/env python

"""
.. module:: analysesTable
     :synopsis: generates a latex table with all analyses.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from ordered_set import OrderedSet

def isIn ( i, txnames ):
    """ is i in list txnames, leaving out onshell versions """
    for x in txnames:
        if i == x: return True
        if i == x+"(off)": return True
    return False

def writeSingleAna ( ana ):
    ret = ""
    lines= [ "" ]
    print ana.globalInfo.id
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
    alltxes = ", ".join ( txnames ) 
    max=30
    if len(alltxes)>max+3:
        alltxes=alltxes[:max]+" ..."

    lines[0] += "%s & %s \\\\\n" % ( ana.globalInfo.id, alltxes )
    return "\\n".join ( lines )

def generateAnalysisTable(listOfAnalyses, texfile=None ):
    """ Generates a raw latex table with all the analyses in listOfAnalyses,
    writes it to texfile (if not None), and returns it as its return value. """

    toprint = """
\\begin{longtable}{|c|c|}
\hline
{\\bf ID} & {\\bf Topologies} \\\\
\hline
"""
    for ana in listOfAnalyses:
        toprint += writeSingleAna ( ana )
    toprint += """
\hline
\caption{SModelS database}
\label{tab:SModelS database} \n \
\end{longtable}
"""

    if texfile:
        outfile = open(texfile,"w")
        outfile.write(toprint)
        outfile.close()
    return toprint

def createPdfFile ( texfile ):
    import commands
    pdffile=texfile.replace(".tex",".pdf" )
    repl="@@@TEXFILE@@@"
    cmd="cat template.tex | sed -e 's/%s/%s/' > /tmp/smodels.tex" % ( repl, texfile )
    commands.getoutput ( cmd )
    commands.getoutput ( "latex /tmp/smodels.tex" )
    os.unlink ( "/tmp/smodels.tex" )
    os.unlink ( "smodels.log" )
    os.unlink ( "smodels.aux" )

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
        argparser.add_argument('-p', '--pdf', help='produce pdf file', 
                            action='store_true' )
        args=argparser.parse_args()
        from smodels.experiment.databaseObj import Database
        database = Database ( args.database )
        #Creat analyses list:
        listOfAnalyses = database.getExpResults()
        #Generate table:
        generateAnalysisTable( listOfAnalyses, texfile=args.output )
        # create pdf
        if args.pdf: createPdfFile ( args.output )

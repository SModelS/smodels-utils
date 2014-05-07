#!/usr/bin/env python

def generateAnalysisTable(ListOfAnalyses, texfile=None, wd=0.15, fig_dir=None):
  """Generates a raw latex table with all the analyses in ListOfAnalyses and their
  respective SMS graphs. The graphs are generated using printAnalysisGraphs.
  If texfile=None, returns the latex table as a single string.
  wd = linewidth of each graph"""



  toprint ="\\begin{longtable}{|c|c|} \n \
  \hline \n\
  Analysis & SMS Topology \\\ \n \
  \hline \n"

  textab = ""
  texlines = []

  if not fig_dir:
    pdf_prefix=None
  else:
    pdf_prefix = fig_dir

  for Ana in ListOfAnalyses:
    texline = Ana.label.partition(":")[0].replace("_","-") + " & "
    resdic = printAnalysisGraphs(Ana,pdf_prefix)
    texconstraint = Ana.results.keys()[0]
    for key in resdic.keys():
      texplot = "\includegraphics[width="+str(wd)+"\linewidth]{"+resdic[key]+"}\spacer"
      texconstraint = texconstraint.replace(key,texplot)

    texline += texconstraint + " \\\ "

    texlines.append(texline)

  newtexlines = []
#Convert simple table to multirow one, grouping the analysis:
  for (iline,line) in enumerate(texlines):
    if line == "Done": continue
    newline = "\multirow{Nrows}{*}{"+line.partition("&")[0]+"} & "+ line.partition("&")[2]
    nrows = 1
    for jline in range(iline+1,len(texlines)):
      lineB = texlines[jline]
      if  line.partition("&")[0] == lineB.partition("&")[0]:
        newline += "\n & " + lineB.partition("&")[2]
        nrows += 1
        texlines[jline] = "Done"

    newline = newline.replace("Nrows",str(nrows))
    newtexlines.append(newline)

  for line in newtexlines:
    textab += line + " \hline \n"

  toprint += textab
  toprint += "\caption{SMS.} \n \
  \label{tab:LHCresults} \n \
  \end{longtable}"

  if texfile:
    outfile = open(texfile,"w")
    outfile.write(toprint)
    outfile.close()
    return True
  else:
    return toprint



def printAnalysisGraphs(Analysis,pdf_prefix=None):
  """ Generateres pdf files with the graph for the SMS Topologies being constrained by the analysis.
  If pdf_prefix=None, uses the analysis label as a prefix for the files."""
  from theory.auxiliaryFunctions import getelements
  from moretools import feynmanGraph
  from theory.SMSDataObjects import EElement

#Get topologies (in string format)
  consts = Analysis.results.keys()
  tops = getelements(consts)
#Get corresponding CMS lables
  CMSlabel = Analysis.plots.values()[0][0]

#Generate file names dictionary:
  topdic = {}
  if not pdf_prefix: pdf_prefix = ""
  pdf_prefix += Analysis.label
  iplot = 0
  for top in tops:
    iplot += 1
    topdic[top] = pdf_prefix + "_" + CMSlabel + "_" + str(iplot) + "_" + ".pdf"
#Generate graph
    feynmanGraph.draw(EElement(top), topdic[top], straight=True, inparts=False )

  return topdic   #Return dictionary

if __name__ == "__main__":
    import setPath, argparse, types, os

    argparser = argparse.ArgumentParser(description='simple tool to generate a latex table with all analysis used')
    argparser.add_argument ( '-o', '--output', nargs='?', help='output file', type=types.StringType, default='tab.tex')
    argparser.add_argument ( '-D', '--Dir', nargs='?', help='figure folder', type=types.StringType, default='figures/')
    args=argparser.parse_args()
    from experiment import smsAnalysisFactory
    #Creat analyses list:
    ListOfAnalyses = smsAnalysisFactory.load()
    if not os.path.isdir(args.Dir):
      os.system("mkdir "+args.Dir)
    #Generate table:
    generateAnalysisTable(ListOfAnalyses, texfile=args.output, fig_dir=args.Dir)


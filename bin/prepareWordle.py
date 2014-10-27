#!/usr/bin/python
# coding=latin-1

""" 

.. module:: prepareWordle
   :synopsis: Script used to create the document for wordle, which is used for
   the banner image, see http://smodels.hephy.at/images/banner.png.  

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com> 

"""

F="/home/walten/Dropbox/Walkding_documentation/PioneerScan/EPJC-revision/pioneer-scan-revised.tex"
f=open(F)
lines=f.readlines()
f.close()

removes=[ "\\bibitem", "\\tilde" , "\\chi", "\\bf", "\\cite", "\\points", "\tt", "\\ref", "\\item", "\\center", "Fig", "$", "\\bar", "\\end", "\\begin", "\\caption", "\\def", "al ", "et ", "\\hline", "\\textwidth", "\\label", "\\large", "\\pm", "\\ensuremath", "fig:", "\\em", "left", "right", "space", "tech", "Rep", "mathbb", "itemize", "finstates", "\\tt" ]
replaces= { "\\mu": "µ", "\\nu":"&nu;" }

w=open("wordle.txt","w")
for line in lines:
  for remove in removes:
    line=line.replace( remove, "" )
  for (From,To) in replaces.items():
    line=line.replace( From, To )
  w.write ( line )
w.close()

import os
os.system ( "cat wordle.txt | xsel" )


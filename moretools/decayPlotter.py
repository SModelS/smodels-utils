#!/usr/bin/env python

"""
.. module:: decayPlotter
    :synopsis: With this module decay plots like 
    http://smodels.hephy.at/images/example_decay.png
    can be created.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com> 

"""

def draw( slhafile, outfile, options, xsecpickle=None, offset=0. ):
  """ draw a decay plot from an slhafile
      :param offset: FIXME what does that one do?
  """
  import set_path
  from moretools import decayPlots
  import os
  out=os.path.basename ( slhafile ).replace(".slha","")
  if outfile!="":
    out=outfile
  # print "out=",out

  for i in [ "leptons", "integratesquarks", "separatecharm", "verbose",
             "dot", "neato", "pdf", "nopng", "nopercentage", "simple", "squarks",\
             "sleptons", "weakinos", "zconstraints", "tex", "color",\
             "masses", "html" ]:
    if not options.has_key ( i ): options[i]=False

  verbosereader=False
  if options["verbose"]==True and not options["html"]: verbosereader=True
  reader=decayPlots.SPhenoReader ( slhafile, verbose=verbosereader, \
      integrateLeptons=(not options["leptons"]),
      integrateSquarks=options["integratesquarks"],
      separatecharm=options["separatecharm"] )

  if options["verbose"]==True and not options["html"]:
    reader.printDecay("~g")
    print reader.getDecays("~g",0.9)

  #tmp=[ "~g" ]
  #tmp.append ("~q" )
  tmp=[  "~g", "~q", "~b", "~t", "~t_1", "~t_2", "~b_1", "~b_2" ]
  if options["squarks"]:
    for i in [ "u", "d", "c", "s", "b", "t", "q" ]:
      for c in ["L", "R", "1", "2" ]:
        tmp.append ("~%s_%s" % ( i, c) )

  if options["sleptons"]:
    for i in [ "l", "e", "mu", "tau", "nu", "nu_e", "nu_mu", "nu_tau" ]:
      for c in ["L", "R", "1", "2" ]:
        tmp.append ("~%s_%s" % ( i, c) )

  if options["weakinos"]:
    tmp.append ("~chi_1+")
    tmp.append ("~chi_2+")
    tmp.append ("~chi_20")
    tmp.append ("~chi_30")

  starters=[]

  for i in tmp:
    if type ( reader.getMass(i) ) == type ( 5.0 ) or type ( reader.getMass(i) ) == type ( 5 ):
      if reader.getMass(i)<100000:
        starters.append ( i )
    else:
      # add all else
      # print i,reader.getMass(i)
      starters.append ( i )

  ### we always go for the pickle file now
  #if False: ## xsecpickle!="" and xsecpickle!=None:
  #  ##print "[visualisePheno] xsecpickle=",xsecpickle
  #  colorizer=decayPlots.XSecFromPickleFile ( xsecpickle )
  #  ## if we got the xsecs from a file, then we can also
  #  ## find the relevant production mechanisms from there
  #  starters=colorizer.relevantProductionParticles
  #else:
  #  colorizer=decayPlots.XSecCalculator ( reader.getMasses() )
  colorizer=decayPlots.ByNameColorizer ( )

 # if options["verbose"]:
 #   if options["html"]: print "<br>"
  #  print "[decayPlotter.py] We start from",starters
  #  if options["html"]: print "<br>"
  ## starters=[ "~q" ]

  ps=reader.getRelevantParticles ( reader.filterNames(starters) )

  ## reader.printDecay ("~g")

  extra={}
  if options["zconstraints"]:
    for i in [ 23, 24 ]:
      ds=reader.getDecays ( i, full=True )
      l=""
      first=True
      for d in ds:
        ## print ds[d].keys()
        l+="%s%s" % ( d, str ( ds[d].keys() ).replace("['","").replace("']","")  )
        if not first:
          l+=", "
        first=False
      if len(l)>0:
        extra[reader.name ( i ) ] = l
  htmlbegin="<font size=-2 color='green'>"
  htmlend="</font>"
  if options["verbose"]:
    if options["html"]: print "<br>",htmlbegin
    print "[decayPlotter] We start from",starters
    if options["html"]: print htmlend,"<br>"
  drawer=decayPlots.Drawer ( options, ps, offset, extra )

  if options["tex"]:
    drawer.tex=True

  #print "Relevant particles:"
  #for name in ps:
  #  print name
  #import sys
  #sys.exit(0)

  #  now construct the nodes and the edges
  for name in ps:
    color="#000000"
    if options["color"]:
      color=colorizer.getColor ( name )
    drawer.addNode ( reader.getMass ( name ), name, \
        options["masses"], color, reader.fermionic ( name ) )
    decs=reader.getDecays ( name, rmin=0.9 )
    drawer.addEdges ( name, decs )

  ## drawer.addMassScale ( )

  if options["verbose"] and options["html"]:
    sout=out
    print htmlbegin,"[decayPlotter] now we draw!",sout,htmlend,"<br>"
  drawer.draw ( out )

  if options["dot"] and options["tex"]:
    if options["verbose"] and options["html"]:
      print htmlbegin,"[decayPlotter] calling dot2tex.<br>",htmlend
    drawer.dot2tex ( out )



if __name__ == "__main__":
  """ the script calls the drawing routine """
  import argparse, types

  argparser = argparse.ArgumentParser(description='SLHA to dot converter.')
  argparser.add_argument ( '-v', '--verbose', help='be verbose',action='store_true' )
  argparser.add_argument ( '-sq', '--squarks',
      help='add squarks to list',action='store_true' )
  argparser.add_argument ( '-sl', '--sleptons',
      help='add sleptons to list',action='store_true' )
  argparser.add_argument ( '-w', '--weakinos',
      help='add weakinos to list',action='store_true' )
  argparser.add_argument ( '-m', '--masses',
      help='add mass labels',action='store_true' )
  argparser.add_argument ( '-Z', '--zconstraints',
      help='write down Z/W decay constraints',action='store_true' )
  argparser.add_argument ( '-P', '--pickle',
      help='get xsecs from pickle file', type=types.StringType, default='' )
  argparser.add_argument ( '-l', '--leptons', help='have separate lepton flavors',\
      action='store_true' )
  argparser.add_argument ( '-i', '--integratesquarks',
      help='sum over different light squark flavors', action='store_true' )
  argparser.add_argument ( '-C', '--separatecharm',
      help='treat charm separately', action='store_true' )
  argparser.add_argument ( '-n', '--neato',
      help='create neato png file',action='store_true' )
  argparser.add_argument ( '-s', '--simple',
      help='simple names -- G instead of ~g, etc',action='store_true' )
  argparser.add_argument ( '--nopercentage',
      help='no percentages at all in labels',action='store_true' )
  argparser.add_argument ( '-N', '--nopng',
      help='dont create dot png file',action='store_true' )
  argparser.add_argument ( '-p', '--pdf',
      help='create dot pdf file',action='store_true' )
  argparser.add_argument ( '-d', '--dot', help='create dot file',action='store_true' )
  argparser.add_argument ( '-t', '--tex', help='tex characters',action='store_true' )
  argparser.add_argument ( '-c', '--color', help='use color',action='store_true' )
  argparser.add_argument ( '-O', '--offset', help='an offset in x in the plot',
                           type=types.IntType, default=0 )
  argparser.add_argument ( '-f', '--filename', nargs='?', \
      help='slha input filename (spheno.slha)',
      type=types.StringType, default="spheno.slha" )

  argparser.add_argument ( '-o', '--outfile', nargs='?', \
      help='output filename (if not specified we use the slha filename '\
           'with a different extension)', type=types.StringType, default="" )
  args=argparser.parse_args()
  Dict=args.__dict__
  options={}
  for (key,value) in Dict.items():
    if type(value)==types.BooleanType:
      options[key]=value

  draw( args.filename, args.outfile, options, args.pickle, args.offset )

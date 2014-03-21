import pygraphviz, sys, math
##  # -*- coding: UTF-8 -*-

class Drawer:
  """ a class that encapsulates the drawing 
  """
  def __init__ ( self, options, ps, offset, extra={}, verbose=False, html=False ):
    self.options=options
    self.maxmass = 10000.
    self.minmass =     0.
    self.massctr=0
    self.extra=extra
    self.offset=offset
    self.massesdrawn=[]
    self.ps=ps
    self.tex=False
    self.G=pygraphviz.AGraph(directed=True)
    self.verbose=verbose
    self.html=html

  def draw ( self, out ):
    print "[drawer.py] draw!!"
    prog=sys.argv[0]
    if prog.rfind("/")>0:
      prog=prog[prog.rfind("/")+1:]
    dprog='dot'
    dargs='-n2 -Tpng:cairo'
    wout=out+".png"
    if self.options["neato"]:
      # wout=out+".neato.png"
      #wout=out+".png"
      #prog='dot'
      #args='-n2 -Tpng:cairo'
      #dargs='-n2'
      #args=''
      prog='neato'
      args='-x -Ln10 -LT1000 -LO -Lg -v'
      if self.options["pdf"]:
        wout=out+".neato.pdf"
    self.G.draw(wout,prog=dprog,args=dargs)
    if self.verbose:
      print "[Drawer.py] %s created with %s." % ( wout, prog )

    if self.options["dot"]:
      # wout=out+".dot"
      wout=out+".dot"
      print "[drawer.py] write to",wout
      self.G.write(wout)
      if self.verbose:
        print "[Drawer.py] %s created with dot." % ( wout )

    #if not self.options["nopng"]:
      ## wout=out+".dot.png"
    #  wout=out+".xxx"
    if self.options["pdf"]:
      # wout=out+".dot.pdf"
      wout=out+".pdf"
      
      self.G.draw(wout,prog='dot')
      if self.verbose:
        print "[Drawer.py] %s created with dot." % ( wout )

  def xvalue ( self, mass, ctr, n_relevant, name ):
    """ where on the axis should particle with mass <mass> go? """
    if name=="~g":
      return 200+self.offset
    ret = 100.
    delta=50.
    if n_relevant < 10:
      delta=100.
    for i in self.massesdrawn:
      if math.fabs ( mass - i ) < 50.:
        ret+=50. # 100.
    self.massesdrawn.append ( mass )
    if mass<200 and n_relevant > 7:
      ret+=300
    if n_relevant < 10:
      ret+=ctr*30.
    return ret

  def addNode ( self, mass, name, include_masses=False,
      color='#FFFFFF', isFermionic=True ):
    """ add a node """
    llabel=self.prettyName ( name )
    if include_masses:
      try:
        llabel+=" (%d)" % mass 
      except:
        llabel+=" (%s)" % str( mass )
    
    label=llabel
    ## massctr+=1
    if mass < self.minmass:
      self.minmass=mass
    if mass > self.maxmass:
      self.maxmass=mass
    self.G.add_node ( name )
    node=self.G.get_node ( name )
    node.attr['color']=color
    self.massctr+=1
    fmass=0.
    try:
      fmass=float(mass)
    except:
      pass
    node.attr['pos']="%f,%f" % ( self.xvalue ( \
          fmass, self.massctr, len(self.ps), name ), fmass )
    node.attr['height']= "0.5"
    node.attr['width']="0.5"
    fillcolor="#ffffff"
    if color=="#ff0000": fillcolor="#ffeeee"
    if color=="#009900": fillcolor="#eeffee"
    if color=="#0000cc": fillcolor="#eeeeff"
    if color=="#d57f28": fillcolor="#ffeedd"
    node.attr['fillcolor']=fillcolor
    node.attr['fontcolor']=color
    node.attr['fillstyle']=3
    node.attr['style']='filled'
    if not isFermionic:
      node.attr['shape']='hexagon' # 'egg'
    node.attr['label']="%s" % label

  def addOneEdge ( self, name, daughter, percentage, label ):
    if percentage < 0.1:
      return
    l=label
    if percentage < 0.9 and not self.options["nopercentage"]:
      if self.tex:
        l+=" "+str(int(100*percentage))+"\%" ## trino
      else:
        l+=" "+str(int(100*percentage))+"%"
    self.G.add_edge ( name, daughter )
    edge=self.G.get_edge ( name, daughter )
    edge.attr['label']=l

  def addEdges ( self, name, decs ):
    for (daughter,right) in decs.items():
      label=""
      first=True
      percentage=0
      for (radiator,r) in right.items():
        if self.ps.count ( name ) and self.ps.count ( daughter ):
          if r < 0.01:
            continue
          if not first:
            label+=","
          rname=self.prettyName(radiator).replace(" ","")
          if self.extra.has_key ( rname ):
            rname += "->" + self.extra[rname]
          percentage+=r
          label+=rname
          first=False
      self.addOneEdge ( name, daughter, percentage, label )

  def addMassScale ( self ):
    """ add a ruler that lists the masses """
    for m in range ( int( math.ceil ( minmass/100.)) *100, \
        int(math.floor ( maxmass/100.))*100+1,100):
      self.G.add_node ( str(m) )
      node=self.G.get_node( str(m) )
      node.attr['pos']="%f,%f" % ( 0, m )
      node.attr['color']='#FFFFFF'
      node.attr['label']=str(m)+' GeV'

  def prettyName ( self, mname ):
    n2=mname
    if n2=="W+":
      n2="W"
    if self.options["simple"]:
      n2=n2.replace("~g","G" )
      n2=n2.replace("~chi_10","N" )
      n2=n2.replace("~chi_1+","C" )
      n2=n2.replace("~t_2","T" )
      n2=n2.replace("~t_1","T" )
      n2=n2.replace("~b_2","B" )
      n2=n2.replace("~b_1","B" )
      n2=n2.replace("~nu_muL","xx {dot m}" )
      n2=n2.replace("~nu","NU" )
      return n2
    if self.tex:
      def tilde(x,y=""):
        return "$\\\\tilde{\\\\mathrm{%s}}%s$" % (x,y)
      n2=n2.replace("~chi_10", tilde("\\chi","_{1}^{0}" ) )
      n2=n2.replace("~chi10", tilde("\\chi","_{1}^{0}" ) )
      n2=n2.replace("~chi_1+","$\\tilde{\\chi}_{1}^{+}$" )
      n2=n2.replace("~chi1+","$\\tilde{\\chi}_{1}^{+}$" )
      n2=n2.replace("~chi_2+","$\\tilde{\\chi}_{2}^{+}$" )
      n2=n2.replace("~chi2+","$\\tilde{\\chi}_{2}^{+}$" )
      n2=n2.replace("~chi_20","$\\tilde{\\chi}_{2}^{0}$" )
      n2=n2.replace("~chi20","$\\tilde{\\chi}_{2}^{0}$" )
      n2=n2.replace("~chi30","$\\tilde{\\chi}_{3}^{0}$" )
      n2=n2.replace("~chi_30","$\\tilde{\\chi}_{3}^{0}$" )
      n2=n2.replace("~chi40","$\\tilde{\\chi}_{4}^{0}$" )
      n2=n2.replace("~chi_40","$\\tilde{\\chi}_{4}^{0}$" )
      n2=n2.replace("~nu_muL",tilde("\\nu","_{mu L}" ) )
      n2=n2.replace("~nu_tauL",tilde("\\nu","_{tau L}" ) )
      n2=n2.replace("~nu_eL",tilde("\\nu","_{eL}" ) )
      n2=n2.replace("~tau_L",tilde("\\tau","_{L}" ) )
      n2=n2.replace("~tau_R",tilde("\\tau","_{R}" ) )
      n2=n2.replace("~mu_L",tilde("\\mu","_{L}" ) )
      n2=n2.replace("~mu_R",tilde("\\mu","_{R}" ) )
      n2=n2.replace("~t_1",tilde("t","_{1}" ) )
      n2=n2.replace("~b_1",tilde("b","_{1}" ) )
      n2=n2.replace("~q_1",tilde("q","_{1}" ) )
      n2=n2.replace("~u_1",tilde("u","_{1}" ) )
      n2=n2.replace("~u_L",tilde("u","_{L}" ) )
      n2=n2.replace("~u_R",tilde("u","_{R}" ) )
      n2=n2.replace("~d_1",tilde("d","_{1}" ) )
      n2=n2.replace("~c_1",tilde("c","_{1}" ) )
      n2=n2.replace("~c_L",tilde("c","_{L}" ) )
      n2=n2.replace("~c_R",tilde("c","_{R}" ) )
      n2=n2.replace("~s_1",tilde("s","_{1}" ) )
      n2=n2.replace("~t_2",tilde("t","_{2}" ) )
      n2=n2.replace("~b_2",tilde("b","_{2}" ) )
      n2=n2.replace("~q_2",tilde("q","_{2}" ) )
      n2=n2.replace("~u_2",tilde("u","_{2}" ) )
      n2=n2.replace("~d_L",tilde("d","_{L}" ) )
      n2=n2.replace("~d_R",tilde("d","_{R}" ) )
      n2=n2.replace("~d_2",tilde("d","_{2}" ) )
      n2=n2.replace("~c_2",tilde("c","_{2}" ) )
      n2=n2.replace("~s_2",tilde("s","_{2}" ) )
      n2=n2.replace("~s_L",tilde("s","_{L}" ) )
      n2=n2.replace("~s_R",tilde("s","_{R}" ) )
      n2=n2.replace("~e_L",tilde("e","_{L}" ) )
      n2=n2.replace("gamma","$\\gamma$" )
      n2=n2.replace("~g",tilde("g") )
      ## if n2[:2]=="nu": n2="\\nu"+n2[2:]## if n2=n2.replace ( "nu", "\\nu" )
      #n2=n2.replace("~nu","\\tilde{\\nu}" )
      # n2=n2.replace("nu","\\\\nu" )
      #print "n2=",n2
      #if n2.find("~")>-1: n2=n2.replace("~","tilde")
      ## n2=n2.replace("\\","\\" )
      return n2
    ### n2=n2.replace ( "+", "" )
    n2=n2.replace ( "chi10", "chi&#8321;&#8304;" )
    n2=n2.replace ( "chi1+", "chi&#8321;+" )
    n2=n2.replace ( "chi2+", "chi&#8322;+" )
    n2=n2.replace ( "chi3+", "chi&#8323;+" )
    n2=n2.replace ( "chi20", "chi&#8322;&#8304;" )
    n2=n2.replace ( "chi30", "chi&#8323;&#8304;" )
    n2=n2.replace ( "chi40", "chi&#8324;&#8304;" )
    n2=n2.replace ( "t_1", "t&#8321;" )
    n2=n2.replace ( "t_2", "t&#8322;" )
    n2=n2.replace ( "b_1", "b&#8321;" )
    n2=n2.replace ( "b_2", "b&#8322;" )
    n2=n2.replace ( "t1", "t&#8321;" )
    n2=n2.replace ( "t2", "t&#8322;" )
    n2=n2.replace ( "b1", "b&#8321;" )
    n2=n2.replace ( "b2", "b&#8322;" )
    n2=n2.replace ( "chi", "&Chi;" )
    n2=n2.replace ( "gamma", "&gamma;" )
    n2=n2.replace ( "nu", "&nu;" )
    n2=n2.replace ( "mu", "&mu;" )
    n2=n2.replace ( "tau", "&tau;" )
    #n2=n2.replace ( "~g", "gluino" )
    return n2

  def dot2tex ( self, out ):
    # import os
    import commands, os
    # self.verbose=True
    #if self.verbose:
    #  print "calling dot2tex now"
    #  if self.html: print "<br>"
    cmd="dot2tex --nominsize -c -traw"
    cmd="dot2tex -c -traw"
    #cmd+=" --docpreamble '\\usepackage{scrextend}\n\\changefontsizes[12pt]{14pt}' "
    cmd+="  --figpreamble '\\begin{Large}' --figpostamble '\\end{Large}'"
    longcmd="%s --preproc %s.dot | %s -o %s.tex" % ( cmd, out, cmd, out )
    output=commands.getoutput( longcmd )
    if self.verbose:
      print "<font color='green'>[Drawer.py] ",longcmd,"<br>"
    #  print "<font color='green'>[Drawer.py] dot2tex",output,"</font><br>"
    pdfcmd="pdflatex -interaction nonstopmode -output-directory %s %s.tex " % ( os.path.dirname ( out ), out )
    #if self.verbose:
    #  print "call pdflatex now: %s" % pdfcmd
    #  if self.html: print "<br>"
    output=commands.getoutput(pdfcmd )
    #if self.verbose:
    #  print "<font color='green'>[Drawer.py]",output,"</font><br>"

  def ladot ( self, out ):
    import os
    print "[vis.py] employ ladot on %s.dot" % out
    os.system("cp %s.dot %s.ladot" % ( out, out ) )
    os.system("ladot %s.ladot" % out )
    doc=open("doc.%s.tex" % out ,"w")
    doc.write ( "\\documentclass[11pt]{article}\n" )
    doc.write ( "\\usepackage{psfrag}\n" )
    doc.write ( "\\begin{document}\n" )
    doc.write ( "\\begin{Large}\n" )
    doc.write ( "\\input{%s.tex}\n" % out )
    doc.write ( "\\includegraphics{%s.ps}\n" % out )
    doc.write ( "\\end{Large}\n" )
    doc.write ( "\\end{document}\n" )
    doc.close()
    os.system ("latex doc.%s.tex" % out )
    os.system ("dvips doc.%s" % out )


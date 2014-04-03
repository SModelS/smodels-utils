import pygraphviz, sys, math
##    # -*- coding: UTF-8 -*-

"""
.. module:: decayDrawer
        :synopsis: Module that contains the decay plotting
        "DecayDrawer" class.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import logging
logger = logging.getLogger(__name__)

class DecayDrawer:
    """ a class that encapsulates the decay plot drawing
    """
    def __init__ ( self, options, ps, offset, extra={}, verbose=False, html=False ):
        self.options=options
        self.maxmass = 10000.
        self.minmass = 0.
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
        logger.info ( "%s created with %s." % ( wout, prog ) )

        if self.options["dot"]:
            # wout=out+".dot"
            wout=out+".dot"
            # print "[drawer.py] write to",wout
            self.G.write(wout)
            logger.info ( "%s created with dot." % ( wout ) )

        #if not self.options["nopng"]:
            ## wout=out+".dot.png"
        #    wout=out+".xxx"
        if self.options["pdf"]:
            # wout=out+".dot.pdf"
            wout=out+".pdf"

            self.G.draw(wout,prog='dot')
            if self.verbose:
                logger.log ( "%s created with dot." % ( wout ) )

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
                l+=" "+str(int(100*percentage))+"\\\\%" ## trino
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

    def simpleName ( self, name ):
        """ simple names for slha names """
        reps = { "~g":"G", "~chi_10":"N", "~chi_1+":"C", "~t_2":"T", "~t_1":"T", 
                 "~b_2":"B", "~b_1":"B", "~nu_muL":"xx {dot m}", "~nu":"NU" }
        for (From,To) in reps.items(): name=name.replace(From,To)
        return name

    def texName ( self, name ):
        """ map slha particle names to latex names """
        def huge(x):
            return "\\\\Huge{\\\\textbf{%s}}" % x
        def large(x):
            return "\\\\large{%s}" % x
        def math(x): return "$%s$" % x
        def tilde(x): ## x is in tilde
            return "\\\\tilde{\\\\mathrm{%s}}" % (x)
        name=name.replace("_","")
        tsup=name[-1:]
        tsub=name[-2:-1]
        second=name[1:2]
        first=name[:1]
        if first=="~" and name.find("chi")>-1: # weakinos
            sup,sub="",""
            if tsup in [ "+", "-", "0" ]: sup="^{%s}" % tsup
            if tsub in [ "1", "2", "3", "4", "5" ]: sub="_{%s}" % tsub
            return huge ( math ( tilde ( "\\\\chi" ) + sup + sub )  )

        squarks = [ "u", "d", "c", "s", "t", "b", "e" ]
        if first=="~" and second in squarks: # squarks and selectron
            sub=""
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup 
            return huge ( math ( tilde ( second ) + sub ) )
        if name[:3]=="~mu": # smuon
            sub=""
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup 
            return huge ( math ( tilde ( "\\\\mu" ) + sub ) )
        if name[:4]=="~tau": # stau
            sub=""
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup 
            return huge ( math ( tilde ( "\\\\tau" ) + sub ) )
        if name=="~g": return huge ( math ( tilde ( "g" ) ) )
        if name[:3]=="~nu": # sneutrinos:
            flavor=name[3:-1]
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup
            if flavor in [ "mu", "tau" ]: sub="_{\\\\%s%s}" % (flavor,sub)
            if flavor in [ "e" ]: sub="_{%s%s}" % (flavor,sub)
            return huge ( math ( tilde ( "\\\\nu" ) + sub ) ) 
        if first=="~": return huge ( math ( tilde ( name[1:] ) ) )
        if name=="gamma": return large ( math ( "\gamma" ) )
        if name=="nu": return large ( math ( "\\\\nu" ) )
        return large ( name )

    def htmlName ( self, name ):
        ### name=name.replace ( "+", "" )
        reps= { "chi10":"chi&#8321;&#8304;", "chi1+":"chi&#8321;+", 
           "chi2+":"chi&#8322;+", "chi3+":"chi&#8323;+", "chi20":"chi&#8322;&#8304;",
           "chi30":"chi&#8323;&#8304;", "chi40":"chi&#8324;&#8304;", 
           "t_1":"t&#8321;", "t_2":"t&#8322;", "b_1":"b&#8321;", "b_2":"b&#8322;", 
           "t1":"t&#8321;", "t2":"t&#8322;", "b1":"b&#8321;", "b2":"b&#8322;", 
           "chi":"&Chi;", "gamma":"&gamma;", "nu":"&nu;", 
           "mu":"&mu;", "tau":"&tau;" }
        for (From,To) in reps.items(): name=name.replace(From,To)
        return name

    def prettyName ( self, mname ):
        """ find pretty names for the slha names """
        name=mname
        if name=="W+":
            name="W"
        if self.options["simple"]:
            return self.simpleName ( name )
        if self.tex:
            return self.texName ( name )
        return self.htmlName ( name )

    def meddleWithTexFile ( self,out ):
        """ this changes the tex file! """
        logger.info ( "[meddleWithTexFile] rewriting tex file!" )
        f=open("%s.tex"%out)
        lines=f.readlines()
        f.close()
        f=open("%s.tex"%out,"w")
        for line in lines:
            if "enlargethispage" in line:
                continue
        f.close()

    def dot2tex ( self, out ):
        # import os
        import commands, os
        logger.info ( "calling dot2tex now" )
        #    if self.html: print "<br>"
        cmd="dot2tex --autosize --nominsize --crop %s.dot -traw -o %s.tex" % (out, out )
        self.meddleWithTexFile(out)
        # cmd="dot2tex -c -traw"
        #cmd+=" --docpreamble '\\usepackage{scrextend}\n\\changefontsizes[12pt]{14pt}' "
        #cmd+="    --figpreamble '\\begin{Large}' --figpostamble '\\end{Large}'"
        #longcmd="%s --preproc %s.dot | %s -o %s.tex" % ( cmd, out, cmd, out )
        logger.info (  "cmd=%s " % cmd )
        output=commands.getoutput( cmd )
        logger.info ( output )
        pdfcmd="pdflatex -interaction nonstopmode %s.tex " % ( out )
        logger.info (  "pdfcmd=%s" % pdfcmd )
        output=commands.getoutput(pdfcmd )
        logger.info ( output )

import pygraphviz, sys, math
##    # -*- coding: UTF-8 -*-

"""
.. module:: decayDrawer
        :synopsis: Module that contains the decay plotting
        "DecayDrawer" class.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
class DecayDrawer:
    """ a class that encapsulates the decay plot drawing
    """
    def __init__ ( self, options, ps, offset, extra={}, verbose="info", html=False ):
        import logging
        self.logger = logging.getLogger(__name__)
        verbosity = verbose.lower()
        levels = { "err": logging.ERROR, "warn": logging.WARN, "info": logging.INFO,
                   "debug": logging.DEBUG }
        logLevel = 0
        for k,v in levels.items():
            if k in verbosity:
                logLevel = v
                self.logger.setLevel ( logLevel )
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
        # print "wout=",wout,"dprog=",dprog,"args=",dargs
        if self.options["nopng"]==False:
            self.G.draw(wout,prog=dprog,args=dargs)
            self.logger.debug ( "%s created with %s." % ( wout, prog ) )

        if self.options["dot"]:
            # wout=out+".dot"
            wout=out+".dot"
            # print "[drawer.py] write to",wout
            self.G.write(wout)
            self.logger.debug ( "%s created with dot." % ( wout ) )

        #if not self.options["nopng"]:
            ## wout=out+".dot.png"
        #    wout=out+".xxx"
        if self.options["pdf"]:
            # wout=out+".dot.pdf"
            wout=out+".pdf"

            self.G.draw(wout,prog='dot')
            self.logger.log ( "%s created with dot." % ( wout ) )

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
        #node.attr['fillcolor']=fillcolor
        node.attr['fontcolor']=color
        #node.attr['fillstyle']=3
        # node.attr['style']='filled'
        node.attr['shape']='none' # 'egg'
        #if not isFermionic:
        #    node.attr['shape']="box" # 'egg'
        node.attr['label']="%s" % label

    def addOneEdge ( self, name, daughter, percentage, label, rmin = 0. ):
        if percentage < rmin:
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

    def addEdges ( self, name, decs, rmin = 0.0 ):
        for (daughter,right) in decs.items():
            label=""
            first=True
            percentage=0
            for (radiator,r) in right.items():
                if list (self.ps).count ( name ) and list(self.ps).count ( daughter ):
                    if r < rmin:
                        continue
                    if not first:
                        label+=","
                    rname=self.prettyName(radiator).replace(" ","")
                    if rname in self.extra.keys ( ):
                        rname += "->" + self.extra[rname]
                    percentage+=r
                    label+=rname
                    first=False
                    # print ( "adding", name, daughter, percentage )
                    self.addOneEdge ( name, daughter, percentage, label, rmin )

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
        reps = { "~g":"G", "~chi_10":"N", "~chi1+":"C", "~t_2":"T", "~t_1":"T",
                 "~b_2":"B", "~b_1":"B", "~nu_muL":"xx {dot m}", "~nu":"NU",
                 "~d_R":"DR", "~s_R": "SR", "~chi2+":"C2", "~chi40":"C4",
                 "~chi2+":"C2", "~chi10":"C1", "~chi30":"C3" }
        nname=name
        for (From,To) in reps.items(): nname=nname.replace(From,To)
        # print name,"->",nname
        return nname

    def texName ( self, name, color = False ):
        """ map slha particle names to latex names
        :param color: add color tag
        """
        if name.find(" ")>-1:
            names=name.split()
            texed=[]
            for n in names:
                texed.append ( self.texName ( n, color ) )
            return " ".join ( texed )
        def huge(x):
            return "\\\\Huge{\\\\textbf{%s}}" % x
        def large(x):
            return "\\\\large{%s}" % x
        def math(x): return "$%s$" % x
        def green(x,usecol):
            if not usecol:
                return x
            return "\\color[rgb]{0,.5,0}%s" % x
        def blue(x,usecol):
            if not usecol:
                return x
            return "\\color[rgb]{0,0,.5}%s" % x
        def brown(x,usecol):
            if not usecol:
                return x
            return "\\color{brown}%s" % x
        def red(x,usecol):
            if not usecol:
                return x
            return "\\color[rgb]{.5,0,0}%s" % x
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
            return huge ( green ( math ( tilde ( "\\\\chi" ) + sup + sub ), color ) )

        if name[:4]=="~tau": # stau
            sub=""
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup
            return huge ( brown ( math ( tilde ( "\\\\tau" ) + sub ), color ) )
        squarks = [ "u", "d", "c", "s", "t", "b", "e" ]
        if first=="~" and second in squarks: # squarks and selectron
            sub=""
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup
            return huge ( blue ( math ( tilde ( second ) + sub ), color ) )
        if name[:3]=="~mu": # smuon
            sub=""
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup
            return huge ( brown ( math ( tilde ( "\\\\mu" ) + sub ), color ) )
        if name=="~g": return huge ( red ( math ( tilde ( "g" ) ), color ) )
        if name[:3]=="~nu": # sneutrinos:
            flavor=name[3:-1]
            if tsup in [ "1" , "2", "L", "R" ]: sub="_{%s}" % tsup
            if flavor in [ "mu", "tau" ]: sub="_{\\\\%s%s}" % (flavor,sub)
            if flavor in [ "e" ]: sub="_{%s%s}" % (flavor,sub)
            return huge ( brown ( math ( tilde ( "\\\\nu" ) + sub ), color ) )
        if first=="~": return huge ( math ( tilde ( name[1:] ) ) )
        if name=="gamma": return large ( math ( "\gamma" ) )
        if name=="nu": return large ( math ( "\\\\nu" ) )
        if name=="mu": return large ( math ( "\\\\mu" ) )
        if name=="tau": return large ( math ( "\\\\tau" ) )
        if name=="h1": return large ( "h" )
        if name=="h2": return large ( "H" )
        if name=="a0": return large ( math("A") )
        if name=="a1": return large ( math("A^{1}") )
        #if name=="nu nu": return large ( math ( "\\\\nu \\\\nu" ) )
        #if name=="nu l": return large ( math ( "\\\\nu l" ) )
        #if name=="l nu": return large ( math ( "l \\\\nu" ) )
        return large ( name )

    def htmlName ( self, name ):
        ### name=name.replace ( "+", "" )
        reps= { "chi10":"chi&#8321;&#8304;", "chi1+":"chi&#8321;+",
           "chi2+":"chi&#8322;+", "chi3+":"chi&#8323;+", "chi20":"chi&#8322;&#8304;",
           "chi30":"chi&#8323;&#8304;", "chi40":"chi&#8324;&#8304;",
           "t_1":"t&#8321;", "t_2":"t&#8322;", "b_1":"b&#8321;", "b_2":"b&#8322;",
           "t1":"t&#8321;", "t2":"t&#8322;", "b1":"b&#8321;", "b2":"b&#8322;",
           "chi":"&Chi;", "gamma":"&gamma;", "nu":"&nu;",
           "mu":"&mu;", "tau":"&tau;", "h1":"h", "h2":"H", "a0": "A",
           "a1": "A<sup>1</sup>" }
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
            # return self.simpleName ( name )
            ret = self.texName ( name, self.options["color"] )
            # print ( "ret", name, ret )
            return ret
        return self.htmlName ( name )

    def meddleWithTexFile ( self,out ):
        """ this changes the tex file! """
        self.logger.debug ( "[meddleWithTexFile] rewriting tex file!" )
        f=open("%s.tex"%out)
        lines=f.readlines()
        f.close()
        f=open("%s.tex"%out,"w")
        for line in lines:
            if "enlargethispage" in line:
                continue
            f.write ( line )
        f.close()

    def dot2tex ( self, out ):
        # import os
        import subprocess, os
        cmd="which dot2tex"
        a = subprocess.getoutput ( cmd )
        if not "dot2tex" in a:
            self.logger.error ( "dot2tex not found! (maybe you need to install it?)" )
            print ( "sudo apt install dot2tex" )
        self.logger.debug ( "calling dot2tex now" )
        #    if self.html: print "<br>"
        cmd="dot2tex --autosize --nominsize --crop %s.dot -traw -o %s.tex" % (out, out )
        # cmd="dot2tex -c -traw"
        #cmd+=" --docpreamble '\\usepackage{scrextend}\n\\changefontsizes[12pt]{14pt}' "
        #cmd+="    --figpreamble '\\begin{Large}' --figpostamble '\\end{Large}'"
        #longcmd="%s --preproc %s.dot | %s -o %s.tex" % ( cmd, out, cmd, out )
        self.logger.debug (  "cmd=%s " % cmd )
        output=subprocess.getoutput( cmd )
        self.logger.debug ( "out=%s" % output )
        self.logger.debug ( "now meddle with tex file" )
        self.meddleWithTexFile(out)
        outdir=os.path.dirname ( out )
        if outdir=="":
            outdir="./"
        pdfcmd="pdflatex -interaction nonstopmode -output-directory %s %s.tex " % \
                ( outdir, out )
        self.logger.debug (  "info, pdfcmd=%s" % pdfcmd )
        output=subprocess.getoutput(pdfcmd )
        self.logger.debug ( output )

        if self.options["nopng"]==False:
            cmd='convert +profile "*" -antialias -density 300x300 %s.pdf %s.png' % ( out, out )
            import subprocess
            o = subprocess.getoutput ( cmd )
            if len(o)>0:
                self.logger.error ( "conversion output %s" % o )

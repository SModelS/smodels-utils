##    # -*- coding: UTF-8 -*-

"""
.. module:: decayDrawer
        :synopsis: Module that contains the decay plotting
        "DecayDrawer" class.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import pygraphviz, sys, math, os
import logging
from smodels_utils.helper import sparticleNames

class DecayDrawer:
    """ a class that encapsulates the decay plot drawing
    """
    def __init__ ( self, options, ps, offset, extra={}, verbose="warn", html=False ):
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
        self.namer = sparticleNames.SParticleNames ( susy = False )

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
        if type(name) == int:
            name = self.texName ( name, dollars=True )
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
        tname = self.texName ( name, dollars=True )
        # print ( "Here1, adding", tname )
        self.G.add_node ( tname )
        node=self.G.get_node ( tname )
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

    def addOneEdge ( self, name, daughter, rmin, labels ):
        """ add one edge with labels, etc """
        l=""
        matrixMode = (len(labels)>2)
        if matrixMode: ## make a matrix
            l="$\\\\begin{matrix}"
        for ctr,L in enumerate(labels):
            percentage,label = L[0], L[1]
            # print ( "perc", percentage, name, daughter, label, ctr, len(labels) )
            if percentage < rmin:
                continue
            if ctr>0 and ctr % 2 != 0:
                l+=",\\,"
            #if matrixMode:
            #    label="$"+label+"$"
            l+=label
            if (percentage < 0.9 or len(labels)>1) and not self.options["nopercentage"]:
                if self.tex:
                    l+="\\,"+str(int(100*percentage))+"\\\\%" ## trino
                else:
                    l+="\\,"+str(int(100*percentage))+"%"
            if ctr % 2 == 1 and ctr != len(labels)-1:
                l+=",\\,\\\\\\\\"
        if matrixMode: ## make a matrix
            l+="\\\\end{matrix}$"
        tn = self.texName ( name, dollars=True )
        d = self.texName ( daughter, dollars=True )
        self.addNode ( 0., d )
        t = self.G.add_edge ( tn, d )
        edge=self.G.get_edge ( tn, d )
        edge.attr['label']=l

    def addEdges ( self, name, decs, rmin = 0.0 ):
        for (daughter,right) in decs.items():
            labels = []
            for (radiator,r) in right.items():
                if list (self.ps).count ( name ) and list(self.ps).count ( daughter ):
                    if r < rmin:
                        continue
                    rname=self.prettyName(radiator).replace(" ","")
                    if rname in self.extra.keys ( ):
                        rname += "->" + self.extra[rname]
                    labels.append ( (r,rname) )
            labels.sort( key=lambda x: x[0], reverse=True )
            self.addOneEdge ( name, daughter, rmin, labels )

    def addMassScale ( self ):
        """ add a ruler that lists the masses """
        for m in range ( int( math.ceil ( minmass/100.)) *100, \
                int(math.floor ( maxmass/100.))*100+1,100):
            #print ( "Here2, adding", m )
            self.G.add_node ( str(m) )
            node=self.G.get_node( str(m) )
            node.attr['pos']="%f,%f" % ( 0, m )
            node.attr['color']='#FFFFFF'
            node.attr['label']=str(m)+' GeV'

    def texName ( self, pid, color = False, dollars = True ):
        """ get tex name for pid 
        :param color: add color tag
        :param dollars: need dollars for math mode
        """

        # print ( "[decayDrawer] find texName for", pid, type(pid) )
        if type(pid)==int:
            ret = self.namer.texColor(pid ) + self.namer.name ( pid )
            if dollars:
                ret = f"${ret}$"
            # print ( "ret=", ret )
            return ret
        return pid

    def htmlName ( self, name ):
        print (  "find htmlName for", name )
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
            ret = self.texName ( name, self.options["color"], dollars=True ) 
            # print ( "ret", name, ret )
            return ret
        return self.htmlName ( name )

    def meddleWithTexFile ( self,out ):
        """ this changes the tex file! """
        fname = "%s.tex"%out 
        if not os.path.exists ( fname ):
            return
        self.logger.debug ( "[meddleWithTexFile] rewriting tex file!" )
        f=open( fname )
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
        self.logger.info (  "%s" % cmd )
        output=subprocess.getoutput( cmd )
        self.logger.debug ( "out=%s" % output )
        self.logger.debug ( "now meddle with tex file" )
        self.meddleWithTexFile(out)
        outdir=os.path.dirname ( out )
        if outdir=="":
            outdir="./"
        pdfcmd="pdflatex -interaction nonstopmode -output-directory %s %s.tex " % \
                ( outdir, out )
        self.logger.error (  "%s" % pdfcmd )
        output=subprocess.getoutput(pdfcmd )
        self.logger.debug ( output )

        if self.options["nopng"]==False:
            args = '+profile "*" -antialias -density 300x300'
            args += ' -background white -flatten'
            cmd='convert %s %s.pdf %s.png' % ( args, out, out )
            import subprocess
            self.logger.info ( cmd )
            o = subprocess.getoutput ( cmd )
            if len(o)>0:
                self.logger.error ( "conversion output %s" % o )

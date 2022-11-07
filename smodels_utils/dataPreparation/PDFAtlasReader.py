#!/usr/bin/env python3

""" A pdf reader class for ATLAS limit plots
"""

import minecart
import sys
import os

class PDFAtlasReader(): 
    def __init__( self, config : dict ): 
        """
        :param config: a dictionary that contains the setup of our task
        """
        self.config = config
        self.config["x"]["delta"]=config["x"]["limits"][1]-config["x"]["limits"][0]
        self.config["y"]["delta"]=config["y"]["limits"][1]-config["y"]["limits"][0]
        self.read()

    def error ( self, line ):
        print ( f"[PDFAtlasReader] Error: {line}" )
        raise RuntimeError( line )

    def pprint ( self, line ):
        print ( f"[PDFAtlasReader] {line}" )

    def pdfToMasses ( self, pdfx, pdfy, round_x = None, round_y = None ):
        """ convert pdfx and pdfy to masses 
        :param round_x: if not None, round to a multiple of this number
        :param round_y: if not None, round to a multiple of this number
        """
        rx = ( pdfx - self.pdf_x0 ) / ( self.pdf_xmax - self.pdf_x0 )
        ry = ( pdfy - self.pdf_y0 ) / ( self.pdf_ymax - self.pdf_y0 )
        x = self.config["x"]["limits"][0] + rx * ( self.config["x"]["delta"] )
        y = self.config["y"]["limits"][0] + ry * ( self.config["y"]["delta"] )
        if round_x != None:
            x = round ( x / round_x ) * round_x
        if round_y != None:
            y = round ( y / round_y ) * round_y
        return x,y

    def computeXYLetter ( self, letter ):
        """ compute X and Y coordinates for letter """
        ## '0.39' bbox (365.7701221858726, 245.44099671225973,
        # 373.6441329278273, 257.6138040553271) sits at 150,150
        ## '0.079' bbox (604.3641221858726, 246.15319671225976,
        # 614.6649340291972, 260.36233437884295) sits at 550,150
        bbox = letter.bbox 
        # pdf_xavg = is the x coordinate in pdf coord system
        pdf_yavg = ( bbox[1] + bbox[1] ) / 2.
        pdf_xavg = ( bbox[0] + bbox[0] ) / 2.
        round_x, round_y = None, None
        if "round" in self.config["x"]:
            round_x = self.config["x"]["round"]
        if "round" in self.config["y"]:
            round_y = self.config["y"]["round"]
        return self.pdfToMasses ( pdf_xavg, pdf_yavg, round_x, round_y )

    def computeXYShape ( self, shape ):
        """ compute X and Y coordinates for shape """
        # pdf_xavg = is the x coordinate in pdf coord system
        path = shape.path
        ret = []
        for pt in path:
            if pt[0] not in [ "m", "l" ]:
                self.pprint ( f"for shape we have '{pt[0]}'" )
            ret.append ( self.pdfToMasses ( pt[1], pt[2] ) )
        return ret
        

    def read ( self ):
        """ read in the file """
        fname = self.config["name"]
        if not fname.endswith ( ".pdf" ):
            fname += ".pdf"
        f = open ( fname, "rb" )
        pdffile = open(fname, 'rb')
        doc = minecart.Document(pdffile)
        page = doc.get_page(0)
        if page == None:
            line = f"cannot retrieve first page of {fname}. Aborting."
            self.error ( line )
        self.page = page
        self.findOffsets()
        self.ulValues()
        self.exclusionLine()

    def findOffsets ( self ):
        """ this is about finding the offsets """
        # pdf_x0 and pdf_y0 are the pdf coordinates of our smallest xs and ys
        # this was a rough guess
        #self.pdf_x0 = ( self.page.letterings[0].bbox[0] + self.page.letterings[0].bbox[2] ) / 2.
        #self.pdf_y0 = self.page.letterings[0].bbox[1] + 25.
        # pdf_xmax and pdf_ymax are the pdf coordinates of our largest xs and ys
        #self.pdf_xmax = self.page.width - 60.
        #self.pdf_ymax = self.page.height - 50.

        for s in self.page.shapes:
            if s.stroke == None:
                continue
            c = s.stroke.color.as_rgb()
            if c != ( 0,0,0 ):
                continue
            dash = s.stroke.dash
            if dash not in [ None, ([], 0) ]:
                continue
            if len(s.path) < 4:
                continue
            lw = s.stroke.linewidth
            ## this is it!
            self.pdf_x0 = s.path[0][1]
            self.pdf_y0 = s.path[0][2]
            self.pdf_xmax = s.path[1][1]
            self.pdf_ymax = s.path[2][2]

            

    def ulValues( self ):
        destname = "ul.csv"
        print ( f"[PDFAtlasReader] writing {destname}" )
        f = open ( destname, "wt" )
        filename = os.path.basename ( self.config['name'] )
        f.write ( f"# upper limit values, extracted from {filename}\n" )
        if "axes" in self.config:
            f.write ( f"# axes are {self.config['axes']}\n" )
        f.write ( f"# x range {self.config['x']}\n" )
        f.write ( f"# y range {self.config['y']}\n" )
        for l,lettering in enumerate(self.page.letterings):
            x, y = self.computeXYLetter ( lettering )
            if False: # lettering.title() in [ "0.39", "0.079", "0.019" ]:
                print ( "letter #", l, "v=", lettering, "bb=", lettering.bbox[:2], "x,y=", self.computeXYLetter ( lettering ) )
            if "." in lettering.title():
                line = f"{x},{y},{lettering.title()}\n"
                if self.yIsDiff():
                    line = f"{x},{x-y},{lettering.title()}\n"
                f.write ( line )
        f.close()

    def isDarkRed ( self, c ):
        """ check if it is the dark red that ATLAS uses for observed limits """
        if abs ( c[0]-0.501961 ) < 1e-5 and abs ( c[1] ) < 1e-5 and \
           abs ( c[2] ) < 1e-5:
                return True
        return False

    def exclusionLine ( self ):
        line=[]
        ct = 0
        for s in self.page.shapes:
            if s.stroke == None:
                continue
            c = s.stroke.color.as_rgb()
            dash = s.stroke.dash
            if self.isDarkRed ( c ) and s.stroke.linewidth > 2.1 and dash == ([], 0):
                ct += 1
                cur = self.computeXYShape ( s ) 
                for pt in cur:
                    if pt[1] < pt[0]:
                        line.append ( pt )
        f=open ( "excl.csv", "wt" )
        for l in line:
            line = f"{l[0]},{l[1]}\n"
            if self.yIsDiff():
                line = f"{l[0]},{l[0]-l[1]}\n"
            f.write ( line )
        f.close()

    def yIsDiff ( self ):
        if "axes" in self.config:
            a = self.config["axes"].strip()
            a = a.replace(" ","")
            if a == "[[x-y],[x-y]]":
                # self.pprint ( "using x-y" )
                return True
        return False

    def interact ( self ):
        import IPython
        IPython.embed ( colors = "neutral" )

 
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="PDF Reader for ATLAS files")
    ap.add_argument('-f', '--file',
            help='pdf file to read [figaux_08a.pdf]', default='figaux_08a.pdf')
    ap.add_argument('-i', '--interactive',
            help="interactive shell", action="store_true" )
    ap.add_argument('-x', '--xrange',
            help='xrange as [min,max,round]', default='[100,850,50]')
    ap.add_argument('-y', '--yrange',
            help='yrange as [min,max,round]', default='[100,850,50]')
    ap.add_argument('-a', '--axes',
            help='axes, e.g. [[x,y],[x,y]]', default='[[x,y],[x,y]]')
    args = ap.parse_args()
    xrange = eval ( args.xrange )
    yrange = eval ( args.yrange )
    xround = None
    yround = None
    if len(xrange)>2:
        xround=xrange[2]
    if len(yrange)>2:
        yround=yrange[2]
    config =  {
        'name': args.file,
        'x':{'limits': ( xrange[0], xrange[1]), 'round': xround },
        'y':{'limits': ( yrange[0], yrange[1]), 'round': yround },
#        'axes': '[[x-y],[x-y]]',
        }

    r = PDFAtlasReader( config )
    if args.interactive:
        r.interact()

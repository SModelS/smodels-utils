#!/usr/bin/env python3

""" A pdf reader class for ATLAS limit plots
"""

import minecart
import sys

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

    def pdfToMasses ( self, pdfx, pdfy ):
        """ convert pdfx and pdfy to masses """
        rx = ( pdfx - self.pdf_x0 ) / ( self.pdf_xmax - self.pdf_x0 )
        ry = ( pdfy - self.pdf_y0 ) / ( self.pdf_ymax - self.pdf_y0 )
        x = self.config["x"]["limits"][0] + rx * ( self.config["x"]["delta"] )
        y = self.config["y"]["limits"][0] + ry * ( self.config["y"]["delta"] )
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
        return self.pdfToMasses ( pdf_xavg, pdf_yavg )

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
        # pdf_x0 and pdf_y0 are the pdf coordinates of our smallest xs and ys
        self.pdf_x0 = ( self.page.letterings[0].bbox[0] + self.page.letterings[0].bbox[2] ) / 2.
        self.pdf_y0 = self.page.letterings[0].bbox[1] + 30.
        # pdf_xmax and pdf_ymax are the pdf coordinates of our largest xs and ys
        self.pdf_xmax = self.page.width - 20.
        self.pdf_ymax = self.page.height - 30.
        self.ulValues()
        self.exclusionLine()

    def ulValues( self ):
        f = open ( "ul.csv", "wt" )
        for l,lettering in enumerate(self.page.letterings):
            x, y = self.computeXYLetter ( lettering )
            #if lettering.title() in [ "0.39", "0.079" ]:
            #    print ( "letter", l, lettering, "xy", self.computeXYLetter ( lettering ) )
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
        IPython.embed ( using = False )

 
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="PDF Reader for ATLAS files")
    ap.add_argument('-f', '--file',
            help='pdf file to read [figaux_08a.pdf]', default='figaux_08a.pdf')
    ap.add_argument('-i', '--interactive',
            help="interactive shell", action="store_true" )
    args = ap.parse_args()
    config =  {
        'name': args.file,
        'x':{'limits': (100, 850)},
        'y':{'limits': (100, 850)},
#        'axes': '[[x-y],[x-y]]',
        }

    r = PDFAtlasReader( config )
    if args.interactive:
        r.interact()

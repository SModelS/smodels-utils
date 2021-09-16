#!/usr/bin/env python3

""" A pdf reader class for ATLAS limit plots
"""

import minecart

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

    def computeXY ( self, letter ):
        """ compute X and Y coordinates for letter """
        ## '0.39' bbox (365.7701221858726, 245.44099671225973,
        # 373.6441329278273, 257.6138040553271) sits at 150,150
        ## '0.079' bbox (604.3641221858726, 246.15319671225976,
        # 614.6649340291972, 260.36233437884295) sits at 550,150
        bbox = letter.bbox 
        # pdf_xavg = is the x coordinate in pdf coord system
        pdf_yavg = ( bbox[1] + bbox[1] ) / 2.
        pdf_xavg = ( bbox[0] + bbox[0] ) / 2.
        ## rx, ry should be the relative coordinates within the plot
        rx = ( pdf_xavg - self.pdf_x0 ) / ( self.pdf_xmax - self.pdf_x0 )
        ry = ( pdf_yavg - self.pdf_y0 ) / ( self.pdf_ymax - self.pdf_y0 )
        x = self.config["x"]["limits"][0] + rx * ( self.config["x"]["delta"] )
        y = self.config["y"]["limits"][0] + ry * ( self.config["y"]["delta"] )
        #y = yavg - self.config["y"]["limits"][0]
        return x,y

    def read ( self ):
        """ read in the file """
        fname = self.config["name"]+".pdf"
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
        f = open ( "values.csv", "wt" )
        for l,lettering in enumerate(page.letterings):
            x, y = self.computeXY ( lettering )
            if lettering.title() in [ "0.39", "0.079" ]:
                print ( "letter", l, lettering, "xy", self.computeXY ( lettering ) )
            if "." in lettering.title():
                f.write ( f"{x},{y},{lettering.title()}\n" )
        f.close()
        self.interact()

    def interact ( self ):
        import IPython
        IPython.embed ( using = False )

 
if __name__ == "__main__":
    config =  {
        'name': 'figaux_08a',
        'x':{'limits': (100, 850)},
        'y':{'limits': (100, 850)},
        }

    r = PDFAtlasReader( config )

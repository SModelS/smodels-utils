#!/usr/bin/env python3

""" code by Robert Schoefbeck, modified and adapted by WW
    https://github.com/schoef/fun/blob/master/python/pdf-to-root/
"""

from math import log, exp

def delta( r, g, b, ct ):
    return abs(ct[0]-r) + abs(ct[1]-g) + abs(ct[2]-b) 

def max_x( shape ):
    return max([x[1] for x in shape.path if x[0]!='h'])
def min_x( shape ):
    return min([x[1] for x in shape.path if x[0]!='h'])
def max_y( shape ):
    return max([x[2] for x in shape.path if x[0]!='h'])
def min_y( shape ):
    return min([x[2] for x in shape.path if x[0]!='h'])

class PDFLimitReader(): 

    def fromPdfToReal ( self, pdf_x, pdf_y, xmin, xmax, ymin, ymax ):
        r_x = ( pdf_x - self.main_x_min ) / (self.main_x_max-self.main_x_min)
        r_y = ( pdf_y - self.main_y_min ) / (self.main_y_max-self.main_y_min)
        x = r_x * (xmax-xmin) + xmin
        y = r_y * (ymax-ymin) + ymin
        return (x,y )


    def processLines ( self, excllines, expected, pm ):
        """ produce points for exclusion lines
        :param excllines: container of shapes containing lines
        :param expected: selected for expected or observed lines
        :param pm: central value (0), or plus (1) or minus (1) one sigma line
        """
        def distance ( p1, p2 ):
            return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
        xmin, xmax, dx = self.data['x']['limits']
        ymin, ymax, dy = self.data['y']['limits']
        points = []
        scol = (0,0,0)
        if expected:
            scol = (1,0,0)
        countUp = 0
        for l in excllines:
            lw = l.stroke.linewidth ## central value has linewidth 3, 
            col = l.stroke.color.as_rgb()
            #if lw > .8: # pm == 0 and expected:
            #    print ( "i have a line with lw", lw, "color", col, "len", len(l.path) )
            if lw < 1.:
                continue
            if len(l.path)==3: ## legend lines
                continue
            # print ( "l", l, lw, col, len(l.path) )
            if col != scol:
                continue
            if pm == 0 and lw > 2.3:
                continue
            if abs(pm) == 1 and abs ( lw - 1.5 ) > 1e-2:
                continue
            if pm < -.5 and countUp == 0:
                countUp += 1
                continue
            if pm > .5 and countUp > 0:
                continue
            pdf_x = min_x ( l )
            pdf_y = min_y ( l )
            pdf_x = ([x[1] for x in l.path if x[0]!='h'])
            pdf_y = ([x[2] for x in l.path if x[0]!='h'])
            for px,py in zip ( pdf_x, pdf_y ):
                x,y = self.fromPdfToReal ( px, py, xmin,xmax,ymin,ymax )
                p = (x,y)
                if len(points)==0:
                    points.append ( (x,y) )
                elif distance ( p, points[-1] ) > 1e-6:
                    points.append ( (x,y) )
            if len(points)>10: ## done
                return points
        return points

    def get_axis_dict( self ):
        import minecart
        # open pdf file
        fname = self.data["name"]#
        if not fname.endswith ( ".pdf" ):
            if not fname.endswith ( "." ):
                fname += "."
            fname+="pdf"
        pdffile = open(fname, 'rb')
        doc = minecart.Document(pdffile)
        page = doc.get_page(0)
        if page == None:
            line = f"cannot retrieve first page of {fname}. Aborting."
            print ( f"[PDFLimitReader] error: {line}" )
            raise RuntimeError( line )

        #Find colored box shapes that share the maximal x coordinate. That's the color legend (z_axis)
        colored_shapes = []
        excllines = []
        for shape in page.shapes:
            ## exclusion lines are red or black
            if shape.stroke is not None:
                if shape.stroke.color.as_rgb() in [ (1,0,0), (0,0,0) ]:
                    excllines.append ( shape )
            # these colored boxes have identical stroke and fill color and are neither black or white
            if shape.fill and shape.stroke and hasattr(shape.stroke, 'color') and shape.stroke.color.as_rgb()==shape.fill.color.as_rgb():
                if shape.fill.color.as_rgb() in [(1,1,1), (0,0,0)]: continue
                #print (shape.fill.color.as_rgb(), len(shape.path))
                if len(shape.path)!=6:
                    raise RuntimeError(f"You need to look at this shape: {shape.path!r}")
                #there are two 'h' objects at the end
                #y_vals.append(shape.path[-3])
                colored_shapes.append(shape)
        pdffile.close()
       
        # global max_x for all appropriately colored shapes 
        max_x_global  = max( map( max_x, colored_shapes ) )

        self.z_axis_shapes = list(filter( lambda s: max_x(s)==max_x_global, colored_shapes ))
        self.z_axis_dict = {}
        for shape in self.z_axis_shapes:
            self.z_axis_dict[tuple(shape.fill.color.as_rgb())] = { 'ymin':shape.path[0][2], 'ymax':shape.path[2][2] }
        self.z_axis_ymax = max( [ d['ymax'] for d in self.z_axis_dict.values() ] )
        self.z_axis_ymin = min( [ d['ymin'] for d in self.z_axis_dict.values() ] )
        self.z_max_color = next( k for k, v in self.z_axis_dict.items() if v['ymax']==self.z_axis_ymax ) 
        self.z_min_color = next( k for k, v in self.z_axis_dict.items() if v['ymin']==self.z_axis_ymin ) 

        # These are the shapes (hopefully rectangular) of the main pad. 
        # I take all non-BW shapes with identical fill and stroke color whose max_x isn't the global maximum of such shapes
        self.main_shapes   = list(filter( lambda s: max_x(s)<max_x_global, colored_shapes ))
        self.minx, self.maxx, self.miny, self.maxy = [], [], [], []
        deltax, deltay = [], []
        for i,ms in enumerate ( self.main_shapes ):
            ix =  min_x ( ms )
            ax =  max_x ( ms )
            iy =  min_y ( ms )
            ay =  max_y ( ms )
            self.minx.append ( ix )
            self.maxx.append ( ax )
            self.miny.append ( iy )
            self.maxy.append ( ay )
            if ax-ix>0.:
                deltax.append ( ax - ix )
            if ay-iy>0.:
                deltay.append ( ay - iy )

        self.deltax = min ( deltax )
        self.deltay = min ( deltay )
        # print ( "deltas", self.deltax, self.deltay )
        # max/min of the coordinates of the shapes in the PDF
        self.main_x_max = max(map(max_x, self.main_shapes))
        self.main_y_max = max(map(max_y, self.main_shapes))
        self.main_x_min = min(map(min_x, self.main_shapes))
        self.main_y_min = min(map(min_y, self.main_shapes))

        exc = {}
        exts= { 0: "", 1: "P1", -1: "M1" }
        for expected in [ False, True ]:
            name = "obsExclusion"
            if expected:
                name = "expExclusion"
            for pm in [ -1, 0, 1 ]:
                exc[name+exts[pm]] = self.processLines ( excllines, expected=expected, pm=pm )
        self.exclusions = exc
        if False:
            for name, values in exc.items():
                print ( "line:", name, values[:3] )
        # for debugging
        #for shape in self.main_shapes:
        #    ct = shape.fill.color.as_rgb()        
        #    best_match = self.get_best_match( *ct )
        #    #print (shape.fill.color.as_rgb(), shape.path)
        #    #print ("best_match", best_match )
        #    print ("delta", delta(*ct, ct=best_match)) 
        #    #print (self.get_z( *ct ))

    def get_best_match( self, r, g, b ):
        return min( list(self.z_axis_dict.keys()), key = lambda ct : delta( r,g,b, ct = ct) )

    def get_z( self, r, g, b):
        # find closest:
        best_match = self.get_best_match( r, g, b )
        # throw some warnings so we know if the plot is strongly capped
        #if (r,g,b)==self.z_max_color:
        #    print("Warning! This is the max color!")
        #if (r,g,b)==self.z_min_color:
        #    print("Warning! This is the min color!")
        return exp( log(self.data['z']['limits'][0]) + (self.z_axis_dict[best_match]['ymin'] - self.z_axis_ymin)/(self.z_axis_ymax-self.z_axis_ymin) * ( log(self.data['z']['limits'][1])  - log(self.data['z']['limits'][0]) ) )

    def get_limit( self, x, y ):
        ''' get limit in the coordinates of the original plot
        '''
        xmin, xmax, dx = self.data['x']['limits']
        ymin, ymax, dy = self.data['y']['limits']
        # normalise to unit interval
        r_x = (x - xmin)/(xmax-xmin)
        r_y = (y - ymin)/(ymax-ymin)

        #print ("r",r_x,r_y)

        # transfrom to PDF coordinates
        pdf_x = self.main_x_min + r_x*(self.main_x_max-self.main_x_min)
        pdf_y = self.main_y_min + r_y*(self.main_y_max-self.main_y_min)

        #print ("pdf",pdf_x,pdf_y)

        # this assumes rectangular shapes!
        this_shape = None
        for i,shape in enumerate(self.main_shapes):
            #if pdf_x>=min_x(shape) and pdf_x<max_x(shape) and pdf_y>=min_y(shape) and pdf_y<max_y(shape):
            if pdf_x>=self.minx[i] and pdf_x<self.maxx[i] and pdf_y>=self.miny[i] and \
               pdf_y<self.maxy[i]:
                this_shape = shape
                # print ("Found")
                break

        if this_shape:
            return self.get_z( *this_shape.fill.color.as_rgb() )
        
    def __init__( self, limit_dict ): 
        self.data = limit_dict
        self.exclusions = { "obsExclusion": [], "expExclusion": [], 
            "obsExclusionP1": [], "obsExclusionM1": [], "expExclusionP1": [], 
            "expExclusionM1": [] }
        self.get_axis_dict()
 
if __name__ == "__main__":
    data =  {
        'name': 'CMS-PAS-SUS-21-009_Figure_009-b',
        'x':{'limits': (1500, 2800, 25) },
        # 'y':{'limits': (0, 3000, 25) },
        'y':{'limits': (0, 2300, 25) },
        'z':{'limits': (10**-1, 40 ), 'log':True},
        'topology': 'T5Hg'
        }

    r = PDFLimitReader( data )
    for i in [ "obsExclusion", "expExclusion", "obsExclusionP1", "obsExclusionM1",
               "expExclusionP1", "expExclusionM1" ]:
        f=open ( f"{data['topology']}_{i}.csv", "wt" )
        pts = r.exclusions[i]
        for pt in pts:
            f.write ( f"{pt[0]},{pt[1]}\n" )
            # f.write ( "%f,%f\n" % ( pt[0],pt[0]-pt[1] ) )
        f.close()
    # get the limit at the bottom right
    print ( "limit at 2200,500 is", r.get_limit(2200,500) )

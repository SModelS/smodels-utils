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

    def get_axis_dict( self ):
        import minecart
        # open pdf file
        pdffile = open(self.data['name']+'.pdf', 'rb')
        doc = minecart.Document(pdffile)
        page = doc.get_page(0)

        #Find colored box shapes that share the maximal x coordinate. That's the color legend (z_axis)
        colored_shapes = []
        for shape in page.shapes:
            # these colored boxes have identical stroke and fill color and are neither black or white
            if shape.fill and shape.stroke and hasattr(shape.stroke, 'color') and shape.stroke.color.as_rgb()==shape.fill.color.as_rgb():
                if shape.fill.color.as_rgb() in [(1,1,1), (0,0,0)]: continue
                #print (shape.fill.color.as_rgb(), len(shape.path))
                if len(shape.path)!=6:
                    raise RuntimeError("You need to look at this shape: %r" % shape.path)
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
        for i,ms in enumerate ( self.main_shapes ):
            self.minx.append ( min_x ( ms ) )
            self.maxx.append ( max_x ( ms ) )
            self.miny.append ( min_y ( ms ) )
            self.maxy.append ( max_y ( ms ) )

        # max/min of the coordinates of the shapes in the PDF
        self.main_x_max = max(map(max_x, self.main_shapes))
        self.main_y_max = max(map(max_y, self.main_shapes))
        self.main_x_min = min(map(min_x, self.main_shapes))
        self.main_y_min = min(map(min_y, self.main_shapes))

        # for debugging
        #for shape in self.main_shapes:
        #    ct = shape.fill.color.as_rgb()        
        #    best_match = self.get_best_match( *ct )
        #    #print (shape.fill.color.as_rgb(), shape.path)
        #    #print ("best_match", best_match )
        #    #print ("delta", delta(*ct, ct=best_match)) 
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
        xmin, xmax = self.data['x']['limits']
        ymin, ymax = self.data['y']['limits']
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
        self.get_axis_dict()
 
if __name__ == "__main__":
    data =  {
        'name': 'CMS-SUS-17-001_Figure_011-a', 
        'x':{'limits': (150, 1200)},
        'y':{'limits': (0, 600)},
        'z':{'limits': (10**-3, 10**2), 'log':True},
        }

    r = PDFLimitReader( data )
    # get the limit at the bottom right
    print (r.get_limit(1199,0))

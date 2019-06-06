#!/usr/bin/env python3

import pickle, subprocess, sys, copy
import numpy as np
import matplotlib
matplotlib.use('Agg')
from mpl_toolkits.mplot3d import axes3d
from matplotlib.ticker import FormatStrFormatter
from matplotlib import cm
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Pool
import math, copy
import helpers

Writer = animation.writers["ffmpeg"]

class Drawer:
    def __init__ ( self, picklefile, nmin, nmax, save ):
        # self.dpi = 200
        # self.dpi = 100
        self.dpi = 75
        self.savePlots = save
        self.nmin = nmin
        self.nmax = nmax
        self.counter = nmin
        self.picklefile = picklefile
        ## the coordinates that we possibly visualise
        self.coordinates = ( 1000006, 1000001, 1000005 )
        ## our current coordinates
        self.current_coordinates = self.coordinates
        # the current coordinates, as indices of self.coordinates
        self.current_indices = ( True, True, True )
        self.getHistory()
        self.initFigure()
        self.history = []

    def initFigure ( self ):
        # plt.style.use("dark_background")
        self.fig = plt.figure(dpi=self.dpi )
        self.ax = self.fig.add_subplot ( 111, projection="3d" )
        self.ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
        self.mMax = 2500.
        self.ax.set_xlim( 0., self.mMax )
        self.ax.set_ylim( 0., self.mMax )
        self.ax.set_zlim( 0., self.mMax )
        self.ax.set_xlabel ( helpers.toLatex(self.coordinates[0],True,True) )
        self.ax.grid(False)
        self.ax.set_ylabel ( helpers.toLatex(self.coordinates[1],True,True) )
        self.ax.set_zlabel ( helpers.toLatex(self.coordinates[2],True,True) )
        self.ax.zaxis.set_visible(False)

        return self.fig

    def next ( self ):
        if self.counter >= self.nmax:
            raise StopIteration ( "reached step #%d" % self.nmax )
        self.draw ( self.counter )
        self.counter+=1

    def getHistory( self ):
        """ load the history """
        f=open( self.picklefile, "rb" )
        walker = pickle.load ( f )
        f.close()
        tmp = [ [0., 0., 0. ] ]
        def getFilteredMass ( m ):
            if m < 5e5:
                return m
            return 0.
        for pt in walker[::10]:
            masses = [ getFilteredMass(pt["masses"][x]) for x in self.coordinates ]
            tmp.append ( masses )
        self.walk = np.array ( tmp )

    def save ( self, plt, ndim, nsteps, j ):
        #azim = -60 + 10 * math.sin ( nsteps * 2* math.pi / 2000. )
        #self.ax.view_init( azim= azim )
        if self.savePlots:
            filename = "pics/%03d%d.png" % ( nsteps-1, j )
            plt.savefig ( filename, dpi=self.dpi )
        # self.ipython()
        for t in self.ax.texts + self.ax.lines:
            t.set_visible(False)

    def ipython ( self ):
        import IPython
        IPython.embed()
        sys.exit()

    def cutCoords ( self, x, f, n ):
        """ cut the last line to fraction f """
        if len(x)<2:
            return x
        rx = copy.deepcopy ( x )
        rx = rx[:n]
        if n==0:
            return rx
        if n < 2:
            rx[-1] = f*rx[-1]
        else:
            rx[-1]=rx[-2]+f*(rx[-1]-rx[-2])
        return rx

    def minMax ( self, coords ):
        """ our own function that returns minimum *and* maximum (as a tuple),
        while disregarding frozen entries """
        if type(coords) == list:
            coords = np.array( coords )
        return min(coords),max(coords[coords<3000])

    def getCoords ( self, j, n ):
        """ get the coordinates of the current point, in the correct number
            of dimensions """
        xc, yc, zc = self.walk[::,0], self.walk[::,1], self.walk[::,2]
        xcoords = self.cutCoords ( xc, (j+1)/10., n )
        ycoords = self.cutCoords ( yc, (j+1)/10., n )
        zcoords = self.cutCoords ( zc, (j+1)/10., n )
        # self.pprint ( "getting coordinates %d/%d: %s" % (j,n,xcoords[0]) )
        return [ xcoords,ycoords,zcoords ]

    def draw( self, n ):
        for j in range(0,10):
            # self.initFigure()
            title = "MCMC walk, after %d steps" % n
            t = self.ax.text( 2800., 7., 0., title, horizontalalignment="center",
                   verticalalignment="bottom", transform = self.ax.transAxes )
            p = [ t ]
            xcoords,ycoords,zcoords = self.getCoords ( j, n )
            for i in range(n):
                p += self.ax.plot( xcoords[i:i+2], ycoords[i:i+2], zcoords[i:i+2], \
                         c=cm.binary(.3+.6*i/n) )
            p += self.ax.plot( [xcoords[-1]], [ycoords[-1]], [zcoords[-1]], "*", color='r' )
            self.ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
            yminmax = self.minMax(ycoords)
            if abs(yminmax[1])<1e-5:
                self.ax.yaxis.set_visible(False)
            else:
                self.ax.yaxis.set_visible(True)

            zminmax = self.minMax(zcoords)
            if abs(zminmax[1])<1e-5:
                # print ( "make z axis invisible" )
                self.ax.zaxis.set_visible(False)
                self.ax.w_zaxis.line.set_lw(0.)
                self.ax.set_zticks([])
                self.ax.set_zlabel ( "" )
                self.ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
                self.ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            else:
                self.ax.zaxis.set_visible(True)
                self.ax.w_zaxis.line.set_lw(0.8)
                panecol = (0.95, 0.95, 0.95, 0.5)
                self.ax.xaxis.set_pane_color( panecol )
                self.ax.yaxis.set_pane_color( panecol )
                self.ax.zaxis.set_pane_color( panecol )
                self.ax.set_zticks( np.arange ( 0., self.mMax+1, 500. ) )
                self.ax.set_zlabel ( helpers.toLatex(self.coordinates[2],True,True) )
                self.ax.zaxis.set_major_formatter(FormatStrFormatter('%d'))

            self.save ( plt, 3, n, j )
            self.history.append ( p )

    def run ( self ):
        try:
            while True:
                self.next()
        except StopIteration:
            pass

    def pprint ( self, *args ):
        """ logging """
        print ( "[draw] %s" % (" ".join(map(str,args))) )

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser( description="plot pics for movie" )
    parser.add_argument("-f", "--file", type=str,
            help='history file to use [history.pcl]', default="history.pcl")
    parser.add_argument("-n", "--nmin", type=int,
            help='first step [1]', default=1 )
    parser.add_argument("-N", "--nmax", type=int,
            help='last step [100]', default=100 )
    parser.add_argument("-c", "--clear", action="store_true",
            help='clear the pics folder before starting' )
    parser.add_argument("-s", "--save", action="store_true",
            help='keep the individual images as pngs in pics/' )
    args = parser.parse_args()
    if args.clear:
        subprocess.getoutput ("rm pics/*png" )
    drawer = Drawer ( args.file, args.nmin, args.nmax, args.save )
    print ( "draw the pics" )
    drawer.run()
    print ( "now animate the thing" )
    animator = animation.ArtistAnimation( drawer.fig, drawer.history, interval=50,
                                          repeat_delay=3000, blit=False )
    animator.save("movie.mp4")
    print ( "mplayer movie.mp4" )

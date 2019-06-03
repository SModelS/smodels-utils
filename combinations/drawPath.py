#!/usr/bin/env python3

import pickle
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
from mpl_toolkits.mplot3d import axes3d
from matplotlib.ticker import FormatStrFormatter
from matplotlib import cm
from matplotlib import pyplot as plt
from multiprocessing import Pool
import math
import copy

# dpi = 200
# dpi = 100
dpi = 75

class Drawer:
    def __init__ ( self, picklefile ):
        self.picklefile = picklefile

    def trim( self, filename ):
        import subprocess
        cmd = "convert -trim %s %s" % ( filename, filename.replace(".png","_trimmed.png") )
        a = subprocess.getoutput ( cmd )
        cmd = "rm %s" % filename 
        a = subprocess.getoutput ( cmd )

    def getHistory( self, addZero = False ):
        f=open( self.picklefile, "rb" )
        walker = pickle.load ( f )
        f.close()
        tmp = []
        for pt in walker:
            tmp.append ( [ pt["masses"][1000006], pt["masses"][1000001],
                           pt["masses"][1000022] ] )
        walk = np.array ( tmp )
        # print ( "walk", walk )
        return walk

    def save ( self, plt, ax, fig, ndim, nsteps, j ):
        filename = "pics/%dd_%03d%d.png" % ( ndim, nsteps, j )
        #azim = -60 + 10 * math.sin ( nsteps * 2* math.pi / 2000. )
        # ax.view_init( azim= -60 )
        plt.savefig ( filename, dpi=dpi )
        # self.trim ( filename )
        plt.clf()
        plt.cla()

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

    def draw3d( self, n = 80 ):
        walk = self.getHistory()
        xc, yc, zc = walk[::,0], walk[::,1], walk[::,2]
        for j in range(0,10):
            fig = plt.figure(dpi=dpi )
            ax = fig.add_subplot ( 111, projection="3d" )
            xcoords=self.cutCoords ( xc, (j+1)/10., n )
            ycoords=self.cutCoords ( yc, (j+1)/10., n )
            zcoords=self.cutCoords ( zc, (j+1)/10., n )
            # print ( "n=",n,"j=",j,"xcoord",len(xcoords) )
            for i in range(n):
                ax.plot( xcoords[i:i+2], ycoords[i:i+2], zcoords[i:i+2], c=cm.binary(.3+.6*i/n) )
            ax.plot( [xcoords[-1]], [ycoords[-1]], [zcoords[-1]], "*", color='r' )
            ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.zaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.set_xlim(min(xcoords),max(xcoords[xcoords<3000]) )
            ax.set_ylim(min(ycoords),min(ycoords[ycoords<3000]) )
            ax.set_zlim(min(zcoords),min(zcoords[zcoords<3000]) )
            ax.set_xlabel ( "$\\theta_1$" )
            ax.set_ylabel ( "$\\theta_2$" )
            ax.set_zlabel ( "$\\theta_3$" )
            ax.grid(False)
            title = "MCMC walk, after %d steps" % n 
            ax.text( 10., 7., 0., title, horizontalalignment="center",
                   verticalalignment="bottom", transform = ax.transAxes )
            self.save ( plt, ax, fig, 3, n, j )
            #del fig
            #del ax

    def draw2d( self, n = 40 ):
        fig = plt.figure(dpi=dpi)
        ax = fig.add_subplot ( 111, projection="3d" )
        walk = self.getHistory()
        xc, yc, zc = walk[::,0], walk[::,1], [0.]*(n+1)
        for j in range(10):
            fig = plt.figure( dpi=dpi )
            ax = fig.add_subplot ( 111, projection="3d" )
            xcoords=self.cutCoords ( xc, (j+1)/10., n )
            ycoords=self.cutCoords ( yc, (j+1)/10., n )
            zcoords=self.cutCoords ( zc, (j+1)/10., n )
            for i in range(n-1):
                ax.plot( xcoords[i:i+2], ycoords[i:i+2], zcoords[i:i+2], c=cm.binary(.3+.6*i/n) )
            ax.plot( [xcoords[n-1]], [ycoords[n-1]], [zcoords[n-1]], "*", color='r' )
            ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            ax.xaxis._axinfo["grid"]['color'] =  (1,1,1,1)
            ax.zaxis.set_visible(False)
            ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.set_xlim(-7, -1)
            ax.set_ylim(2, 8)
            ax.set_zlim(0, 5)
            ax.set_xlabel ( "$\\theta_1$" )
            ax.set_ylabel ( "$\\theta_2$" )
            ax.w_zaxis.line.set_lw(0.)
            ax.grid(False)
            ax.set_zticks([])
            title = "MCMC walk, after %d steps" % n 
            ax.text( 10., 7., 0., title, horizontalalignment="center",
                   verticalalignment="bottom", transform = ax.transAxes )
            self.save ( plt, ax, fig, 2, n, j )
            #del fig
            #del ax

    def draw1d( self, n = 5 ):
        fig = plt.figure( dpi=dpi )
        ax = fig.add_subplot ( 111, projection="3d" )
        walk = self.getHistory( addZero = True )
        xc, yc, zc = walk[::,0], [0.]*(n+1), [0.]*(n+1)
        for j in range(10):
            fig = plt.figure( dpi=dpi )
            ax = fig.add_subplot ( 111, projection="3d" )
            xcoords=self.cutCoords ( xc, (j+1)/10., n )
            ycoords=self.cutCoords ( yc, (j+1)/10., n )
            zcoords=self.cutCoords ( zc, (j+1)/10., n )
            for i in range(n):
                ax.plot( xcoords[i:i+2], ycoords[i:i+2], zcoords[i:i+2], c=cm.binary(.3+.6*i/n) )
            ax.plot( [xcoords[-1]], [ycoords[-1]], [zcoords[-1]], "*", color='r' )
            ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
            ax.xaxis._axinfo["grid"]['color'] =  (1,1,1,1)
            ax.zaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
            ax.set_ylim(0, 0)
            ax.set_xlim(-7, -1)
            ax.set_zlim(0, 5)
            ax.set_xlabel ( "$\\theta_1$" )
            ax.w_zaxis.line.set_lw(0.)
            ax.w_yaxis.line.set_lw(0.)
            ax.grid(False)
            ax.set_zticks([])
            ax.set_yticks([])
            title = "MCMC walk, after %d steps" % n 
            ax.text( 10., 7., 0., title, horizontalalignment="center",
                   verticalalignment="bottom", transform = ax.transAxes )
            self.save ( plt, ax, fig, 1, n, j )
            # del fig
            # del ax

    def draw ( self, dim, n ):
        if dim == 1:
            self.draw1d ( n )
        if dim == 2:
            self.draw2d ( n )
        if dim == 3:
            self.draw3d ( n )

    def drawAll( self ):
        self.draw1d ( n=1 )
        self.draw1d ()
        with Pool(1) as p:
            p.map ( draw1d, range (0,100 ) )
        self.draw2d ( n=40 )
        self.draw3d ( n=80 )
        self.draw2d ( n = 100 )
        with Pool(1) as p:
            p.map ( self.draw2d, range(500,600) )
        self.draw3d ( n = 200 )
        self.draw3d ( n = 1000 )
        with Pool(1) as p:
            p.map ( self.draw3d, range(1000) )

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser( description="plot pics for movie" )
    parser.add_argument("-f", "--file", type=str, 
            help='history file to use [history.pcl]', default="history.pcl")
    parser.add_argument("-d", "--dimensions", type=int, 
            help='how many dimensions', default=3 )
    parser.add_argument("-nmin", "--nmin", type=int, 
            help='first step [1]', default=1 )
    parser.add_argument("-nmax", "--nmax", type=int, 
            help='last step [100]', default=100 )
    args = parser.parse_args()
    drawer = Drawer ( args.file )
    for i in range(args.nmin,args.nmax):
        drawer.draw ( args.dimensions, i )
    # drawer.drawAll()

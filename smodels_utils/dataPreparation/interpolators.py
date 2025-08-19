#!/usr/bin/env python

"""
.. module:: interpolators
   :synopsis: code to play with various interpolations between grid points
   in UL (EM) grids.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from typing import Union

def interpolate ( p1 : dict, p2 : dict, xi : Union[float,str]="half", method : str = "expo" ):
    """ interpolate between point1(x,y) and point2(x,y) at x.
    :param p1: dict, eg { "x": 1, "y": 2 }
    :param p2: dict, eg { "x": 1, "y": 2 }
    :param xi: value to interpolate for, or "half"
    :returns: interpolated value at x
    """
    if xi == "half": 
        xi= .5*p1["x"]+.5*p2["x"]
    from scipy.interpolate import interp1d
    import numpy as np
    import copy
    p1 = copy.deepcopy ( p1 )
    p2 = copy.deepcopy ( p2 )
    if method=="expo":
        p1["y"]= np.log ( p1["y"] )
        p2["y"]= np.log ( p2["y"] )
    x= [ p1["x"], p2["x"] ]
    y= [ p1["y"], p2["y"] ]
    interp = interp1d(x,y, kind='linear')
    y_new = interp(xi)
    if method == "expo":
        y_new = np.exp(y_new)
    return { "x": xi, "y": float(y_new) }

if __name__ == "__main__":
    ## 5 gev line
    p1 = { "x": 100, "y": 1.460000E+00 }
    p2 = { "x": 125, "y": 1.200000E+00 }
    p3 = { "x": 150, "y": 1.260000E+00 }
    p3 = { "x": 175, "y": 1.270000E+00 }
    p3 = { "x": 200, "y": 1.060000E+00 }
    p3 = { "x": 225, "y": 1.360000E+00 }
    print ( "p1", p1 )
    print ( "p2", p2 )
    expo = interpolate( p1, p2, "half", "expo" )
    lin = interpolate( p1, p2, "half", "linear" )
    print ( "expo", expo )
    print ( "lin", lin )

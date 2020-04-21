#!/usr/bin/env python3

"""
.. module:: rerunOlderValidations
   :synopsis: rerun only validations that are older

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import glob, os, time

def apr18(): ## unix time stamp for april 18
    return time.time()-60*60*24*4

def scan():
    # dictfiles = glob.glob ( "../../smodels-database/13TeV/*/*/validation/T*.py")
    dictfiles = glob.glob ( "../../smodels-database/*TeV/*/*/validation/T*.py")
    anas = set()
    for d in dictfiles:
        D = d.replace("../../smodels-database/","")
        m = os.stat ( d ).st_mtime
        dt = m - apr18()
        p = D.find ( "/validation" )
        ana = D[:p]
        pr = ana.rfind("/")
        ana = ana[pr+1:]
        if dt < 0.:
            anas.add ( ana )
    print ( ",".join ( anas ) )
    # print ( "\n".join ( anas ) )
    print ( "%d analyses need to rerun" % ( len(anas) ) )

if __name__ == "__main__":
    scan()

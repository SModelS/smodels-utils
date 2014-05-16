#!/usr/bin/python

"""
.. module:: countCitations
   :synopsis: a trivial script/module that counts the citations in inspirehep

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def count():
    N=1269436 ## our inspire number
    import urllib2
    U="http://inspirehep.net/record/%d/citations" % N
    f=urllib2.urlopen( U )
    lines=f.readlines()
    f.close()
    for line in lines:
        pos=line.find("Cited by:")
        pos2=line.find("records")
        if pos>-1:
            T=int(line[pos+9:pos2])
    return T

if __name__ == "__main__":
    print count()

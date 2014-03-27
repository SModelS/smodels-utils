#!/usr/bin/python

""" a trivial script that counts the citations in inspirehep """

N=1269436

import urllib2

f=urllib2.urlopen("http://inspirehep.net/record/%d/citations" % N )
lines=f.readlines()
f.close()

for line in lines:
    pos=line.find("Cited by:")
    pos2=line.find("records")
    if pos>-1:
        T=int(line[pos+9:pos2])
        print T

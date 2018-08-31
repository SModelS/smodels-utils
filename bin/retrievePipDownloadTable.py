#!/usr/bin/env python3

""" get the data from the pip download table, export as csv. """

import urllib.request

f=urllib.request.urlopen("http://pepy.tech/project/smodels")
lines=f.readlines()
f.close()

isInTable = False
hasPassedTotal = False

lastDate="1970-07-01"

for line in lines:
    sline=line.decode().strip()
    if len(sline)==0:
        continue
    if not hasPassedTotal and "Total downloads" in sline:
        hasPassedTotal = True
    if not hasPassedTotal:
        continue
    if "<tr>" in sline or "</tr>" in sline:
        continue
    if not isInTable and "<tbody" in sline:
        isInTable = True
        continue
    if isInTable and "/tbody" in sline:
        isInTable = False
    sline = sline.replace("<td>","").replace("</td>","")
    if not isInTable:
        continue
    if "-" in sline:
        lastDate = sline
    else:
        print ( "%s, %s" % ( lastDate, sline ) )

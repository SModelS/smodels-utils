#!/usr/bin/env python3

""" get the data from the pip download table, export as csv. """

import urllib.request
import subprocess

f=urllib.request.urlopen("http://pepy.tech/project/smodels")
lines=f.readlines()
f.close()

isInTable = False
hasPassedTotal = False

lastDate="1970-07-01"

subprocess.getoutput ( "cp ../log/pip_downloads.log ../log/pip_backup.log" )
g=open("../log/pip_downloads.log","r")
oldlines = g.readlines()
g.close()
datefirst = None
if len(oldlines)>0:
    first = str(oldlines[0])
    datefirst = first.split (",")[0]

g=open("../log/pip_downloads.log","w")

ctr = 0
for line in lines:
    sline=line.decode().strip()
    print ( f"line >>>{line}<<<" )
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
        thisline = f"{lastDate}, {sline}"
        ctr+=1
        if ctr<10:
            print ( thisline )
        if lastDate > datefirst:
            g.write ( thisline + "\n" )

for line in oldlines:
    g.write ( str(line) )
g.close()

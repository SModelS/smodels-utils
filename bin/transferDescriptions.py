#!/usr/bin/python

from short_descriptions import SDs
import os, sys, glob

dbf = "/home/walten/git/smodels-database"

def convert ( string ):
    ret = string.replace ( "&ge;", ">=" )
    ret = ret.replace ( "&alpha;", "alpha" )
    ret = ret.replace ( ",,T,,", "_T" )
    ret = ret.replace ( ",,T2,,", "_T2" )
    ret = ret.replace ( ",,CT,,", "_CT" )
    return ret

files = glob.glob ( "%s/*/*/*/globalInfo.txt" % dbf )
for fle in files:
    print ( fle )
    f=open (fle,"r" )
    lines=f.readlines()
    f.close()
    g=open ( fle,"w" )
    Id = None
    ret = []
    hasPrettyName = False
    for line in lines:
        if "id:" in line:
            Id=line.replace("id: ","" ).strip()
            print ( "Id=>%s<" % Id )
        if "prettyName" in line and Id in SDs.keys():
            oldline=line
            line = "prettyName: %s\n" % SDs[Id]
            print ( "replacing %s -> %s" % ( oldline, line ) )
            hasPrettyName = True
        ret.append ( line )
    newlines = ret
    if not hasPrettyName and Id in SDs.keys():
        newlines = []
        for l in ret:
            newlines.append ( l )
            if "lumi:" in l:
                newlines.append ( "prettyName: %s\n" % convert(SDs[Id]) )
    g.write ( "".join ( newlines ) )
    g.close()

files = glob.glob ( "%s/*/*/*/convert.py" % dbf )
for fle in files:
    print ( fle )
    f=open (fle,"r" )
    lines=f.readlines()
    f.close()
    g=open ( fle,"w" )
    Id = None
    ret = []
    hasPrettyName = False
    for line in lines:
        if "MetaInfoInput" in line and "info" in line:
            pos1=line.find( "('" )
            pos2=line.find( "')" )
            Id=line[pos1+2:pos2]
            print ( "Id=>%s<" % Id )
        if "info.prettyName" in line and Id in SDs.keys():
            hasPrettyName = True
            oldline=line
            line = "info.prettyName = '%s'\n" % SDs[Id]
            print ( "replacing %s -> %s" % ( oldline, line ) )
        ret.append ( line )
    newlines = ret
    if not hasPrettyName and Id in SDs.keys():
        newlines = []
        for l in ret:
            newlines.append ( l )
            if "info.lumi" in l:
                newlines.append ( "info.prettyName = '%s'\n" % convert(SDs[Id]) )
    g.write ( "".join ( newlines ) )
    g.close()

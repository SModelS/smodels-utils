#!/usr/bin/python

""" a small script that takes the descriptions from short_descriptions.py,
    and feeds them into the database. WW """

from short_descriptions import SDs
import os, sys, glob

dbf = "/home/walten/git/smodels-database"

ext=".test"
ext=""

def convert ( string ):
    ret = string.replace ( "&ge;", ">=" )
    ret = ret.replace ( "&alpha;", "alpha" )
    ret = ret.replace ( ",,T,,", "_T" )
    ret = ret.replace ( ",,T2,,", "_T2" )
    ret = ret.replace ( ",,CT,,", "_CT" )
    return ret

files = glob.glob ( f"{dbf}/*/*/*/globalInfo.txt" )
for fle in files:
    print ( fle )
    f=open (fle,"r" )
    lines=f.readlines()
    f.close()
    g=open ( fle + ext ,"w" )
    Id = None
    ret = []
    hasPrettyName = False
    for line in lines:
        if "id:" in line:
            Id=line.replace("id: ","" ).strip()
            print ( f"Id=>{Id}<" )
        if "prettyName" in line and Id in SDs.keys():
            oldline=line
            line = f"prettyName: {convert(SDs[Id])}\n"
            print ( f"replacing {oldline} -> {line}" )
            hasPrettyName = True
        ret.append ( line )
    newlines = ret
    if not hasPrettyName and Id in SDs.keys():
        newlines = []
        for l in ret:
            newlines.append ( l )
            if "lumi:" in l:
                newlines.append ( f"prettyName: {convert(SDs[Id])}\n" )
    g.write ( "".join ( newlines ) )
    g.close()

files = glob.glob ( f"{dbf}/*/*/*/convert.py" )
for fle in files:
    print ( fle )
    f=open (fle,"r" )
    lines=f.readlines()
    f.close()
    g=open ( fle + ext , "w" )
    Id = None
    ret = []
    hasPrettyName = False
    for line in lines:
        if "MetaInfoInput" in line and "info" in line:
            pos1=line.find( "('" )
            pos2=line.find( "')" )
            Id=line[pos1+2:pos2]
            print ( f"Id=>{Id}<" )
        if "info.prettyName" in line and Id in SDs.keys():
            hasPrettyName = True
            oldline=line
            line = f"info.prettyName = '{convert(SDs[Id])}'\n"
            print ( f"replacing {oldline} -> {line}" )
        ret.append ( line )
    newlines = ret
    if not hasPrettyName and Id in SDs.keys():
        newlines = []
        for l in ret:
            newlines.append ( l )
            if "info.lumi" in l:
                newlines.append ( f"info.prettyName = '{convert(SDs[Id])}'\n" )
    g.write ( "".join ( newlines ) )
    g.close()

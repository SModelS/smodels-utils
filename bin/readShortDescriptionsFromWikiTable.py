#!/usr/bin/python

""" take wiki tables, and extract short description names for analyses from it. """
    
import sys

f=open("short_descriptions" )
lines=f.readlines()
f.close()

D={}

for line in lines:
    tokens = line.split ( "||" )
    if len(tokens)<2:
        continue
    name = tokens[1]
    name = name[name.find("|")+1:-3].strip()
    if name=="": continue
    description= tokens[2].strip()
    if description == "": continue
    D[name]=description

f=open ( "short_descriptions.py", "w" )
f.write ( "SDs=%s\n" % (D) )
f.close()

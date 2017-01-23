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
    # name = name[name.find("|")+1:-3].strip()
    name = name[name.find("|")+1:name.find("]")].strip()
    if name=="" or "'''" in name: continue
    description= tokens[2].strip()
    if description == "": continue
    if "_{" in description and "}" in description:
        pin = description.find("_")
        pout = description.find("}")
        description=description[:pin]+",,"+description[pin+2:pout] + ",," + description[pout+1:]
    description = description.replace ( ">=", "&ge;" )
    description = description.replace ( "<=", "&le;" )
    description = description.replace ( "alpha_T", "&alpha;,,T,," )
    # description = description.replace ( "mu", "&mu;" )
    # description = description.replace ( "ETmiss", "<strike>E&ile;" )
    D[name]=description

f=open ( "short_descriptions.py", "w" )
f.write ( "SDs=%s\n" % (D) )
f.close()

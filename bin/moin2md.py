#!/usr/bin/env python3

""" very simple script to ease the transition from moin to markdown """

import sys
import re
fname=sys.argv[1]

f=open(fname)
lines=f.readlines()
f.close()

for l in lines:
    # l = l.replace("<<BR>>","<BR>" )
    l = l.replace("<<BR>>","" )
    l = l.replace("'''","'")
    if l.startswith ( "==" ):
        l="#" + l[2:]
    l = l.replace ( "==", "" )
    l = l.replace ( ",,2,,", "<sub>2</sub>" )
    l = l.replace ( "smodels.hephy.at", "www.hephy.at/user/wwaltenberger/smodels/" )
    l = l.replace ( "{{", '<img src="' )
    l = l.replace ( "}}", " />" )
    l = l.replace ( "||width", '" width' )
    l = l.replace ( ",align", ' align' )
    l = l.replace ( "||", "|" )
    l=l.strip()
    if l == "----":
        l = "-----------------------------"
    if len(l)==0: continue
    b = re.match ( "(.*)\[\[(.*)\|(.*)\]\](.*)", l )
    if b:
        l = l.replace ( "[[" + b.group(2) + "|", "[@@@@@]" )
        l = l.replace ( b.group(3)+"]]", "(" + b.group(2) + ")" )
        l = l.replace ( "@@@@@", b.group(3) )
    print ( l )

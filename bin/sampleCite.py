#!/usr/bin/python

from __future__ import print_function

import bibtexparser

def findCollaboration ( entry ):
    collaboration=""
    ID = entry["ID"]
    if "collaboration" in entry.keys():
        t = entry["collaboration"]
        if "ATLAS" in t:
            collaboration = "ATLAS"
        if "CMS" in t:
            collaboration = "CMS"
    else:
        if "ATLAS" in ID:
            collaboration = "ATLAS"
        if "CMS" in ID:
            collaboration = "CMS"
    return collaboration

def create ( entries, experiment ):
    ret = "% Use this latex code to cite all "+experiment+" results\n"
    ret+= "% \cite{"
    for entry in entries:
        ID = entry["ID"]
        collaboration = findCollaboration ( entry )
        if not experiment == collaboration:
            continue
        ret += "%s, " % ID
    ret = ret[:-2]+"}"
    return ret

def main ():
    f=open("database.bib")
    print ( "\ndatabase.bib:" )
    bibtex=bibtexparser.load ( f )
    f.close()
    print ( create ( bibtex.entries, "CMS" ) )
    print ( create ( bibtex.entries, "ATLAS" ) )
    print ( "\nreferences-fastlim.bib:" )
    f=open("references-fastlim.bib")
    bibtex=bibtexparser.load ( f )
    f.close()
    # print ( create ( bibtex.entries, "CMS" ) )
    print ( create ( bibtex.entries, "ATLAS" ) )

main()

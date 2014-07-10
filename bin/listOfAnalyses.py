#!/usr/bin/env python

"""
.. module:: listOfAnalyses
         :synopsis: Small script to produce the ListOfAnalyses wiki page

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import setPath
from smodels_tools import SModelSTools
from smodels_tools.tools import databaseBrowser
import logging
logger=logging.getLogger(__name__)
    
# browser = databaseBrowser.Browser ( '../../smodels-database/' )
browser = databaseBrowser.Browser ( )
f=open("ListOfAnalyses","w")

def header():
    f.write ( 
## """#acl +DeveloperGroup:read,write,revert -All:write +All:read Default 
"""#acl +DeveloperGroup:read,write,revert -All:write,read Default 
<<LockedPage()>>

= List Of Analyses =
List of analyses and topologies in the SMS results database that has been used in [[http://link.springer.com/article/10.1140/epjc/s10052-014-2868-5|EPJC May 2014, 74:2868]].
It has been created with the [[http://smodels.hephy.at/gitweb/?p=smodels-tools.git;a=blob;f=bin/smsDictionary.py;h=25451211ccf1d38e98c34b9d42e44deb39c6d6ea;hb=refs/heads/develop|listOfAnalyses.py]] tool. 
The list has been created from the database version %s.
There is also an SmsDictionary.

 * Has Condition: lists, whether a special condition is required in order for the constraint to be applicable.
 * Data published in digital form: has the experiment published the data in digital form? (e.g. as a ROOT file, or a HEPDATA table).

To experiment: [[#CMS|CMS]], [[#ATLAS|ATLAS]]

""" % browser.databaseVersion )

def xsel():
    import os
    cmd="cat ListOfAnalyses | xsel -i"
    os.system ( cmd )
    print cmd

def experimentHeader ( experiment, categories ):
    f.write ( "\n" )
    f.write ( "== %s ==\n" % experiment )
    f.write ( "<<Anchor(%s)>>\n" % experiment )

def main():
    header()
    browser.verbosity='error'
    print "Base=",browser.base
    anas = browser.allAnalyses()
    for experiment in [ "CMS", "ATLAS" ]:
        categories=None
        experimentHeader ( experiment, categories )

    xsel()
    
if __name__ == '__main__':
    main()    

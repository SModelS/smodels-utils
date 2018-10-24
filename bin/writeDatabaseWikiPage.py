#!/usr/bin/python3

from __future__ import print_function
import sys, os, glob, json, string, re


class Del:
  def __init__(self, keep=string.digits):
    self.comp = dict((ord(c),c) for c in keep)
  def __getitem__(self, k):
    return self.comp.get(k)

DD = Del()

def xsel( ):
    cmd="cat Databases | xsel -i"
    os.system ( cmd )
    print ( cmd )
    
def sizeof_fmt(num, suffix='B'):                                              
    for unit in [ '','K','M','G','T','P' ]:                                   
        if abs(num) < 1024.:                                                  
            return "%3.1f%s%s" % (num, unit, suffix)                          
        num /= 1024.0                                                         
    return "%.1f%s%s" % (num, 'Yi', suffix)

def oldheader( w ):
    """ the old header, in moin moin wiki syntax, for smodels.hephy.at """
    w.write(
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default
<<LockedPage()>>

= Public databases =

This page lists all databases that are accessible via http://smodels.hephy.at/database/XXX, where XXX is the database name:

||<#EEEEEE:> '''Name''' ||<#EEEEEE:> '''Description''' ||<#EEEEEE:> '''Frozen''' ||<#EEEEEE:> '''Fastlim''' ||<#EEEEEE:> '''Size''' ||<#EEEEEE:> '''URL''' ||
""" )


def header( w ):
    w.write(
"""# Public databases

This page lists all databases that are accessible via http://smodels.hephy.at/database/XXX, where XXX is the database name:

| **Name** | **Description** | **Frozen** | **Fastlim** | **Size** | **URL** |
| -------- | --------------- | ---------- | ----------- | -------- | ------- |
""" )

def footer ( w ):
    w.write ( """
Unfrozen databases are synched automatically.
""" )

def main():
    """ the wiki page, in markdown syntax. fit for github.com """
    w=open("Databases","w" )
    header ( w )
    Dir = "/var/www/database/"
    globs=list ( glob.glob("%s*" % Dir ) )
    globs.sort()

    for filen in globs:
        if ".pcl" in filen: continue
        dbname = filen.replace(Dir,"" )
        # Ver = dbname.translate(DD)
        m = re.search("\d",dbname)
        if m == None:
            Ver = dbname.translate(DD)
        else:
            Ver = dbname[m.start():]
        ver2 = Ver[2:].replace("_fastlim","")
        ver = "v" + Ver[0]+"."+Ver[1]+"."+ver2
        description="[Official database, %s](ListOfAnalyses%s%s%s)" % ( ver, Ver[0],Ver[1],ver2 )
        j = json.load ( open(filen) )
        size=sizeof_fmt ( j["size"] )
        frozen="yes"
        url="http://smodels.hephy.at/database/%s" % dbname
        if "test" in filen:
            continue ## skip them
            description = "Small test database, %s" % ver
        if "unittest" in filen:
            continue ## skip them
            description = "Database used for unit tests, %s" % ver
        fastlim="no"
        if "fastlim" in Ver:
            fastlim="yes"
        # fastlim="&#10004;"
        w.write ( "| %s | %s | %s | %s | %s | %s |\n" % \
                  ( dbname, description, frozen, fastlim, size, url ) )
    footer ( w )
    w.close()
    xsel()


def oldmain():
    """ the old main, for moin moin wiki, as used in smodels.hephy.at """
    w=open("Databases","w" )
    oldheader ( w )
    Dir = "/var/www/database/"
    globs=list ( glob.glob("%s*" % Dir ) )
    globs.sort()

    for filen in globs:
        if ".pcl" in filen: continue
        dbname = filen.replace(Dir,"" )
        # Ver = dbname.translate(DD)
        m = re.search("\d",dbname)
        if m == None:
            Ver = dbname.translate(DD)
        else:
            Ver = dbname[m.start():]
        ver2 = Ver[2:].replace("_fastlim","")
        ver = "v" + Ver[0]+"."+Ver[1]+"."+ver2
        description="[[ListOfAnalyses%s%s%s|Official database, %s]]" % ( Ver[0],Ver[1],ver2, ver )
        j = json.load ( open(filen) )
        size=sizeof_fmt ( j["size"] )
        frozen="yes"
        url="http://smodels.hephy.at/database/%s" % dbname
        if "test" in filen:
            continue ## skip them
            description = "Small test database, %s" % ver
        if "unittest" in filen:
            continue ## skip them
            description = "Database used for unit tests, %s" % ver
        fastlim="no"
        if "fastlim" in Ver:
            fastlim="yes"
        # fastlim="&#10004;"
        w.write ( "|| %s || %s || %s || %s || %s || %s ||\n" % \
                  ( dbname, description, frozen, fastlim, size, url ) )
    footer ( w )
    w.close()
    xsel()

oldmain()

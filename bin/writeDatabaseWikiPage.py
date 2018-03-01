#!/usr/bin/python3

from __future__ import print_function
import sys, os, glob, json, string


class Del:
  def __init__(self, keep=string.digits):
    self.comp = dict((ord(c),c) for c in keep)
  def __getitem__(self, k):
    return self.comp.get(k)

DD = Del()

def xsel( ):
    cmd="cat Database | xsel -i"
    os.system ( cmd )
    print ( cmd )
    
def sizeof_fmt(num, suffix='B'):                                              
    for unit in [ '','K','M','G','T','P' ]:                                   
        if abs(num) < 1024.:                                                  
            return "%3.1f%s%s" % (num, unit, suffix)                          
        num /= 1024.0                                                         
    return "%.1f%s%s" % (num, 'Yi', suffix)

def header( w ):
    w.write(
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default
<<LockedPage()>>

= Public databases =

This page lists all databases that are accessible via http://smodels.hephy.at/database/XXX, where XXX is the database name:

||<#EEEEEE:> '''Name''' ||<#EEEEEE:> '''Description''' ||<#EEEEEE:> '''Frozen''' ||<#EEEEEE:> '''Size''' ||<#EEEEEE:> '''URL''' ||
""" )

def footer ( w ):
    w.write ( """
The (unfrozen) databases are synched automatically.
""" )

def main():
    w=open("Database","w" )
    header ( w )
    Dir = "/var/www/database/"
    globs=glob.glob("%s*" % Dir )

    for filen in globs:
        if ".pcl" in filen: continue
        dbname = filen.replace(Dir,"" )
        ver = dbname.translate(DD)
        ver = "v" + ver[0]+"."+ver[1]+"."+ver[2:]
        description="Official database, %s" % ver
        j = json.load ( open(filen) )
        size=sizeof_fmt ( j["size"] )
        frozen="yes"
        url="http://smodels.hephy.at/database/%s" % dbname
        if "test" in filen:
            description = "Small test database, %s" % ver
        if "unittest" in filen:
            description = "Database used for unit tests, %s" % ver
        w.write ( "|| %s || %s || %s || %s || %s ||\n" % \
                  ( dbname, description, frozen, size, url ) )
    footer ( w )
    w.close()
    xsel()

main()

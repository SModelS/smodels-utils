#!/usr/bin/python

from __future__ import print_function
import sys
import commands
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database

def xsel():
    import os
    cmd="cat SubDimensionalResults | xsel -i"
    os.system ( cmd )
    print ( cmd )

def backup():
    o = commands.getoutput ( "cp SubDimensionalResults OldSubDimensionalResults" )
    if len(o):
        print ( "backup: %s" % o )

def diff():
    o = commands.getoutput ( "diff SubDimensionalResults OldSubDimensionalResults" )
    if len(o)==0:
        print ( "No changes in SubDimensionalResults since last call." )
        return
    print ( "SubDimensionalResults has changed (%d changes)" % ( len(o.split() ) ) )

def header( f, version ):
    f.write (
# """#acl +DeveloperGroup:read,write,revert -All:write,read Default
# <<LockedPage()>>
"""#acl +DeveloperGroup:read,write,revert -All:write +All:read Default

= List Of Sub-Dimensional Results =
The following is a list of SMS results with unphysical constraints,
e.g. a result for a cascade decay applies only if the mass of
the intermediate particle is exactly the means of the mother and
the daughter masses. For realistic applications, these results
are not applicable. They are anyhow kept in the SModelS database
for reasons of documentation and completeness.

The list has been created from the database version `%s`.

""" % version )

def tableHeader ( f ):
    fields = [ "id", "topology", "constraint" ]
    for i in fields:
        f.write ( "||<#EEEEEE:> '''%s'''" % i )
    f.write ( "||\n" )

def writeEntry ( f, id, tx ):
    f.write ( "|| %s || %s || %s ||\n" % ( id, tx.txName, tx.getInfo("axes") ) )

def main():
    backup()
    f=open("SubDimensionalResults","w")
    d=Database("../../smodels-database/")
    header( f, d.databaseVersion )
    tableHeader ( f )

    for expRes in d.getExpResults():
        expResId = expRes.globalInfo.id
        topos = []
        for dataset in expRes.datasets:
            dsId = dataset.dataInfo.dataId
            for txname in dataset.txnameList:
                txn = txname.txName
                data_dim = txname.txnameData.dimensionality
                full_dim = txname.txnameData.full_dimensionality
                if (data_dim,full_dim) == (2,6):
                    topos.append ( txname )
        for topo in topos:
            writeEntry ( f, expResId, topo )
    f.close()
    diff()
    xsel()

if __name__ == "__main__":
    main()

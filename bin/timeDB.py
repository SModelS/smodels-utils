#!/usr/bin/python3

import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
from smodels.installation import version
import numpy

try:
    import commands as executor
except:
    import subprocess as executor


f=open("log%s" % version(),"w")
# dir = "./database/"
dir = "../../smodels-database/"

def write ( line ):
    f.write ( line + "\n" )
    print ( line )

write ( "version: %s" % version() )

pcl = "%sdatabase.pcl" % dir

if os.path.exists ( pcl ):
    os.unlink ( pcl )

t0=time.time()
write ( "start" )
d=Database( dir )
write( str(d) )
t1=time.time()
write ( "Building the database took %.2f seconds." % ( t1 - t0 ) )
s = os.stat ( pcl )
write ( "Database is %.1f MB." % ( s.st_size / 1000. / 1000. ) )
d=Database( dir )
t2=time.time()
write ( "Reading the database took %.2f seconds." % ( t2 - t1 ) )

statistics = []

for i in range(10):
    executor.getoutput ( "sudo /home/walten/.local/bin/drop_caches.sh" )
    t3=time.time()

    d=Database( dir )
    t4=time.time()
    dt = t4 - t3
    write ( "Reading the database (flushed) took %.2f seconds." % dt )
    statistics.append ( dt )

write ( "avg time reading database: %.2f +- %.2f" % \
        ( numpy.mean(statistics), numpy.sqrt ( numpy.var ( statistics ) ) ) )

write ( "done" )
f.close()

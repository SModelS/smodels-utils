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


f=open(f"log{version()}","w")
# dir = "./database/"
dir = "../../smodels-database/"

def write ( line ):
    f.write ( f"{line}\n" )
    print ( line )

write ( f"version: {version()}" )

pcl = f"{dir}database.pcl"

if os.path.exists ( pcl ):
    os.unlink ( pcl )

t0=time.time()
write ( "start" )
d=Database( dir )
write( str(d) )
t1=time.time()
write ( f"Building the database took {t1 - t0:.2f} seconds." )
s = os.stat ( pcl )
write ( f"Database is {s.st_size / 1000.0 / 1000.0:.1f} MB." )
d=Database( dir )
t2=time.time()
write ( f"Reading the database took {t2 - t1:.2f} seconds." )

statistics = []

for i in range(10):
    executor.getoutput ( "sudo /home/walten/.local/bin/drop_caches.sh" )
    t3=time.time()

    d=Database( dir )
    t4=time.time()
    dt = t4 - t3
    write ( f"Reading the database (flushed) took {dt:.2f} seconds." )
    statistics.append ( dt )

write ( "avg time reading database: %.2f +- %.2f" % \
        ( numpy.mean(statistics), numpy.sqrt ( numpy.var ( statistics ) ) ) )

write ( "done" )
f.close()

#!/usr/bin/python3

import sys, os, time
sys.path.insert(0,"../")
from smodels.experiment.databaseObj import Database
try:
    import commands as executor
except:
    import subprocess as executor


f=open("log","w")
# dir = "./database/"
dir = "../../smodels-database/"

pcl = "%sdatabase.pcl" % dir

if os.path.exists ( pcl ):
    os.unlink ( pcl )

t0=time.time()
d=Database( dir )
f.write(d+"\n" )
t1=time.time()
f.write ( "Building the database took %.2f seconds.\n" % ( t1 - t0 ) )
s = os.stat ( pcl )
f.write ( "Database is %.1f MB.\n" % ( s.st_size / 1000. / 1000. ) )
d=Database( dir )
t2=time.time()
f.write ( "Reading the database took %.2f seconds.\n" % ( t2 - t1 ) )

executor.getoutput ( "sudo /home/walten/.local/bin/drop_caches.sh" )
t3=time.time()

d=Database( dir )
t4=time.time()
f.write ( "Reading the database (flushed) took %.2f seconds.\n" % ( t4 - t3 ) )
f.close()
print ( "done" )

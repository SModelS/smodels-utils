#!/usr/bin/env python3

from smodels.experiment.databaseObj import Database
from smodels.tools.physicsUnits import GeV
import socket
import atexit

servers = []

def shutdown ():
    print ( "[databaseServer] shutting down servers" )
    for i in servers:
        i.finish()

class DatabaseServer:
    def __init__ ( self, dbpath, port ):
        self.dbpath = dbpath
        self.port = port
        self.packetlength = 256
        servers.append ( self )

    def run ( self ):
        self.initialize()

    def parseData ( self, data ):
        """ parse the data packet """
        data=data[2:-1]
        self.pprint ( 'received "%s"' % data )
        if not data.startswith ( "query " ):
            self.pprint ( "I dont understand the data packet %s" % data )
            return
        data=data[6:] ## remove the query statement
        ret = self.lookUpResult ( data )
        self.pprint ( 'sending result of "%s" back to the client' % ret )
        ret = (str(ret)+" "*32)[:32]
        self.connection.sendall ( bytes(ret,"utf-8") )

    def lookUpResult ( self, data ):
        tokens = data.split(":")
        anaId, dType, txname = tokens[1], tokens[2], tokens[3]
        massv = eval(tokens[4])
        for ibr,br in enumerate(massv):
            for iel,el in enumerate(br):
                    massv[ibr][iel]=el*GeV
        expected = False 
        if tokens[0] == "exp":
            expected = True
        self.pprint ( 'looking up result for %s %s %s %s' % ( anaId, txname, dType, massv ) )
        for exp in self.expResults:
            if not exp.globalInfo.id == anaId:
                continue
            for ds in exp.datasets:
                if dType == "ul" and ds.getType() != "upperLimit":
                    continue
                if dType != "ul" and dType != ds.getID():
                    continue
                if dType != "ul" and ds.getType() != "efficiencyMap":
                    continue
                for txn in ds.txnameList:
                    if txn.txName != txname:
                        continue
                    coords = txn.txnameData.dataToCoordinates ( massv, txn.txnameData._V,
                             txn.txnameData.delta_x ) 
                    res = None
                    if expected:
                        if txn.txnameDataExp != None:
                            res = txn.txnameDataExp.getValueForPoint ( coords )
                    else:
                        res = txn.txnameData.getValueForPoint ( coords )
                    print ( "now query", massv, anaId, ds.getType(), txname, ":", res )
                    return str(res)
        return "None"

    def finish ( self ):
        if hasattr ( self, "connection" ):
            self.connection.close()

    def listen ( self ):
        try:
            self.pprint ( 'connection from', self.client_address )

            # Receive the data in small chunks and retransmit it
            while True:
                data = self.connection.recv( self.packetlength )
                if data:
                    self.parseData ( str(data) )
                else:
                    self.pprint ( 'no more data from %s:%s' % \
                                  ( self.client_address[0], self.client_address[1] ) )
                    break
        finally:
            # Clean up the connection
            self.finish()

    def pprint ( self, *args ):
        print ( "[databaseServer]", " ".join(map(str,args)) )

    def initialize( self ):
        self.db = Database ( self.dbpath )
        self.expResults = self.db.expResultList
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('localhost', self.port )
        self.pprint ( 'starting up on %s port %s' % self.server_address )
        self.pprint ( 'I will be serving database %s at %s' % \
                      (self.db.databaseVersion, self.dbpath ) )
        self.sock.bind( self.server_address )

        # Listen for incoming connections
        self.sock.listen(1)

        atexit.register ( shutdown )

        while True:
            # Wait for a connection
            self.pprint ( 'waiting for a connection' )
            self.connection, self.client_address = self.sock.accept()
            self.listen()

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='an instance of a database server' )
    argparser.add_argument ( '-d', '--dbpath',
            help='The database path [./original.pcl]',
            type=str, default="./original.pcl" )
    argparser.add_argument ( '-p', '--port',
            help='port to listen to [31770]',
            type=int, default=31770 )
    args = argparser.parse_args()
    server = DatabaseServer ( args.dbpath, args.port )
    server.run()

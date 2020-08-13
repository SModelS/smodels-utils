#!/usr/bin/env python3

import socket, sys

class DatabaseClient:
    def __init__ ( self, dbpath, port ):
        self.dbpath = dbpath
        self.port = port
        self.packetlength = 256

    def run ( self ):
        self.initialize()
        self.send()

    def send ( self ):
        try:
            
            # Send data
            # message = b'query obs:ATLAS-SUSY-2016-07:ul:T1:[[5.5000E+02,4.5000E+02],[5.5000E+02,4.5000E+02]]'
            message = b'query obs:ATLAS-SUSY-2013-05:ul:T2bb:[[300,100],[300,100]]'
            self.pprint ( 'sending "%s"' % message )
            self.sock.sendall(message)

            # Look for the response
            amount_received = 0
            amount_expected = len(message)
            
            self.pprint ( 'sent message' )
            
            while amount_received < amount_expected:
                data = self.sock.recv( self.packetlength )
                amount_received += len(data)
                self.pprint ( 'received "%s"' % data )

        finally:
            self.pprint ( 'closing socket' )
            self.sock.close()

    def pprint ( self, *args ):
        print ( "[databaseClient]", " ".join(map(str,args)) )

    def initialize( self ):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        self.server_address = ('localhost', self.port )
        self.pprint ( 'connecting to %s port %s' % self.server_address )
        self.sock.connect( self.server_address )

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='an instance of a database client' )
    argparser.add_argument ( '-d', '--dbpath',
            help='The database path [./original.pcl]',
            type=str, default="./original.pcl" )
    argparser.add_argument ( '-p', '--port',
            help='port to listen to [31770]',
            type=int, default=31770 )
    args = argparser.parse_args()
    client = DatabaseClient ( args.dbpath, args.port )
    client.run()

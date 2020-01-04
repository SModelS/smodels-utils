#!/usr/bin/env python3

""" script to check if we can lock a certain file """

import sys, fcntl, argparse

def main():
    fname = sys.argv[1]
    print ( "open", fname )
    f=open( fname, "rb" )
    print ( "lock" )
    fcntl.flock ( f, fcntl.LOCK_EX | fcntl.LOCK_NB )
    print ( "unlock" )
    fcntl.flock ( f, fcntl.LOCK_UN )
    print ( "done" )

main()

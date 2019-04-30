#!/usr/bin/env python3

""" Thin out validation points, i.e. remove points that 
are too close to other points. """

import subprocess
import argparse
import glob

def main():
    ap = argparse.ArgumentParser(description="Thin out validation tarballs.")
    ap.add_argument ( '-t', '--topo', 
            help='specify the topology to be thinned out.',
            default = 'T5WW', type = str )

if __name__ == "__main__":
    main()

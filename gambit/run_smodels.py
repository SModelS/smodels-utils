#!/usr/bin/env python3

""" a first version of a backend for gambit """

import os

def run_smodels ( slhafile : os.PathLike ):
    pass

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="first candidate for gambit/colliderbit SModelS backend")
    run_smodels ( slhafile )

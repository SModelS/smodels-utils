#!/usr/bin/env python3

""" simple script that perpetually updates hiscore list
    from H<n>.pcl, and trims leading model """

import time, types
import hiscore


def updateHiscores():
    args = types.SimpleNamespace()
    args.print = True
    args.detailed = False
    args.interactive = False
    args.trim_branchings = True
    args.trim = True
    args.fetch = False
    args.analysis_contributions = True
    args.check = False
    args.nmax = 1
    args.outfile = "hiscore.pcl"
    args.infile = None
    args.maxloss = .005
    hiscore.main ( args )

def updateStates():
    args = types.SimpleNamespace()
    args.print = True
    args.detailed = False
    args.interactive = False
    args.trim_branchings = False
    args.trim = False
    args.fetch = False
    args.analysis_contributions = False
    args.check = False
    args.nmax = 20
    args.outfile = "states.pcl"
    args.infile = None
    args.maxloss = .005
    hiscore.main ( args )

def main():
    while True:
        updateHiscores()
        updateStates()
        time.sleep(1200.)

main()

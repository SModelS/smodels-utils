#!/usr/bin/env python3

""" simple script that perpetually updates hiscore list
    from H<n>.pcl, and trims leading model """

import time, types
import hiscore


def update():
    args = types.SimpleNamespace()
    args.print = True
    args.detailed = False
    args.interactive = False
    args.trim_branchings = True
    args.trim = True
    args.fetch = False
    args.analysis_contributions = True
    args.check = False
    args.nmax = 10
    args.outfile = "hiscore.pcl"
    args.infile = None
    args.maxloss = .005
    hiscore.main ( args )

def main():
    while True:
        update()
        time.sleep(600.) ## only every 10 mins

main()

#!/usr/bin/env python3

def queryStats ( maxsteps = None ):
    import running_stats
    running_stats.count_jobs()
    running_stats.running_stats()
    if maxsteps != None:
        for i in range(maxsteps):
            time.sleep(30.)
            print()
            running_stats.count_jobs()
            running_stats.running_stats()
            print()

def describeSetup():
    import scipy
    print ( f"scipy {scipy.__version__}" )

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a walker")
    argparser.add_argument ( '-q','--query',
            help='query status, dont actually run (use -M to query repeatedly)',
            action="store_true" )
    argparser.add_argument ( '-s','--setup',
            help='check the setup',
            action="store_true" )
    args=argparser.parse_args()
    if args.query:
        queryStats ( )
    if args.setup:
        describeSetup()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

""" clears out old temp files """

import os, time, glob, shutil

def clear( hours : int, verbose : bool ):
    """
    :param hours: minimum age for deletion, in hours
    """
    files = glob.glob ( "tmp*" )
    files += glob.glob ( "_V*" )
    files += glob.glob ( "../clip/temp/_V*" )
    files += glob.glob ( f"{os.environ['OUTPUTS']}/_V*" )
    # files += glob.glob ( "pythia*" )
    t0=time.time()
    for f in files:
        timestamp = ( t0 - os.stat ( f ).st_mtime ) / 60 / 60.
        if timestamp > hours:
            print ( f"deleting {f}: {timestamp:.1f} hours old" )
            try:
                shutil.rmtree ( f )
            except NotADirectoryError as e:
                os.unlink ( f )
        else:
            if verbose:
                print ( f"keeping {f}: {timestamp:.1f} hours old" )


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Remove temp dirs above a certain age" )
    ap.add_argument('-t', '--time',
            help='minimum age in hours [72]',
            default = 72, type = int)
    ap.add_argument('-v', '--verbose',
            help='verbose', action="store_true" )
    args = ap.parse_args()
    clear ( args.time, args.verbose )

if __name__ == "__main__":
    main()

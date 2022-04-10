#!/usr/bin/env python3

"""
.. module:: extractFromCrashFile
         :synopsis: simple script that extracts files from a crash report

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>


"""

import os

def extractFrom ( crashfile ):
    """ perform the extraction on crashfile """
    if not os.path.exists ( crashfile ):
        print ( f"[extractFromCrashFile] could not find {crashfile}" )
        return
    f=open(crashfile,"rt")
    lines=f.readlines()
    f.close()
    isInFile = None
    skipper = 0 # used for skipping lines
    fhandle = None
    for i,line in enumerate(lines):
        if skipper > i: # skipping!!
            continue
        if isInFile == None:
            for starter in [ "* Input File", "* Parameter File" ]:
                if line.startswith ( starter):
                    isInFile = lines[i+1].strip()
                    skipper = i+4
                    fhandle = open ( isInFile, "wt" )
                    print ( f"[extractFromCrashFile] extracting {isInFile}" )
            if isInFile != None:
                continue
        if isInFile == None and line.startswith("* Output" ):
            isInFile = "output"
            skipper = i+2
            fhandle = open ( isInFile, "wt" )
            print ( f"[extractFromCrashFile] extracting {isInFile}" )
            continue
        if isInFile != None:
            # we are in a file!!
            if line.startswith ( "-"*80 ): # we close the file
                fhandle.close()
                isInFile = None
            else:
                # print ( "writing", line, "to", isInFile )
                fhandle.write ( line )

def extract():
    import argparse
    argparser = argparse.ArgumentParser(description='simple script that extracts files from a crash report' )
    argparser.add_argument ( '-c', '--crashfile', help='input crash file [input.crash]',
                             type=str, default='input.crash' )
    args = argparser.parse_args()
    extractFrom ( args.crashfile )

if __name__ == "__main__":
    extract()

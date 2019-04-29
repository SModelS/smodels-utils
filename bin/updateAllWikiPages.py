#!/usr/bin/env python3

## a super simple script to update all wiki pages in a single go.

import sys, subprocess, argparse, os, colorama

def execute(cmd):
    print ( "[cmd] %s" % " ".join ( cmd ) )
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

def exec(cmd):
    for line in execute ( cmd ):
        print ( line, end="" )

def gprint ( line ):
    print ( "%s%s%s" % ( colorama.Fore.GREEN, line, colorama.Fore.RESET ) )

def main():
    import argparse
    argparser = argparse.ArgumentParser(
            description='Bulk update of all wiki pages. Calls listOfAnalyses.py, ../validation/createWikiPage.py, smsDictionary.py, publishDatabasePickle.py.')
    argparser.add_argument ( '-n', '--non_versioned', 
            help='update the non-versioned files also (eg Validation.md, not just Validation211.md)',
            action='store_true' )
    argparser.add_argument ( '-f', '--feynman', help='also create Feynman Graphs when calling smsDictionary',
                             action='store_true' )
    argparser.add_argument ( '-P', '--no_pickle', 
            help='Skip creation of pickle files',
            action='store_true' )
    argparser.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
    A = argparser.parse_args()
    db = "~/git/smodels-database/"
    ref_db = "~/git/smodels-database-release/"
    db = os.path.expanduser( db )
    ref_db = os.path.expanduser( ref_db )
    ## list of analyses, with and without superseded
    gprint ( "\nCreate list of analyses" )
    cmd = [ "./listOfAnalyses.py", "-a" ]
    if A.ignore:
        cmd += [ "-i" ]
    exec ( cmd )
    exec ( cmd + [ "-n" ] )
    if A.non_versioned:
        print ( "Update also the non-versioned files" )
        cmd = [ "./listOfAnalyses.py" ]
        if A.ignore:
            cmd += [ "-i" ]
        exec ( cmd )
        exec ( cmd + [ "-n" ] )
        #exec ( [ "./listOfAnalyses.py" ] )
        #exec ( [ "./listOfAnalyses.py", "-n" ] )
    else:
        print ( "Update only versioned files" )

    ## SmsDictionary page
    gprint ( "\nCreate SmsDictionary" )
    cmd = [ "./smsDictionary.py", "-a" ]
    if A.feynman:
        cmd += [ "-f", "-c" ]
    exec ( cmd )
    if A.non_versioned:
        exec ( [ "./smsDictionary.py" ] )

    if not A.no_pickle:
        print ( "\nCreate and publish database pickle" )
        exec ( [ "./publishDatabasePickle.py", "-b", "-f", db ] )
        exec ( [ "./publishDatabasePickle.py", "-r", "-b", "-f", db ] )

    gprint ( "create Validation wiki" )
    cmd = [ "../validation/createWikiPage.py", "-c", ref_db ]
    if A.ignore:
        cmd += [ "-i" ]
    exec ( cmd + [ "-a", "-s", "-f" ] )
    exec ( cmd + [ "-a", "-u" ] )
    if A.non_versioned:
        exec ( cmd + [ "-s", "-f" ] )
        exec ( cmd + [ "-u" ] )


if __name__ == "__main__":
    main()

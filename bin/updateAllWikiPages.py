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

def exec(cmd, dry_run ):
    if dry_run:
        print ( f"Dry-run: Would execute {' '.join(cmd)}" )
        return
    for line in execute ( cmd ):
        print ( line, end="" )

def gprint ( line ):
    print ( "%s%s%s" % ( colorama.Fore.GREEN, line, colorama.Fore.RESET ) )

def gitPush( dry_run ):
    cmd = "cd ../../smodels.github.io/; git pull; git commit -am 'automated update'; git push"
    print ( "[updateAllWikiPages.py] %s" % cmd )
    if dry_run:
        return
    o = subprocess.getoutput ( cmd )
    print ( "[updateAllWikiPages.py] %s" % o )

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
    argparser.add_argument ( '-d', '--dry_run', 
            help='dry run, write commands, do not execute them',
            action='store_true' )
    argparser.add_argument ( '-c', '--commit', 
            help='git-commit and git-push to smodels.github.io',
            action='store_true' )
    argparser.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
    A = argparser.parse_args()
    db = "~/git/smodels-database/"
    db = os.path.expanduser(db)
    if not os.path.exists(db):
        db = "~/tools/smodels-database/"
        db = os.path.expanduser(db)
    ref_db = "~/git/smodels-database-release/"
    ref_db = os.path.expanduser( ref_db )
    ## list of analyses, with and without superseded
    gprint ( "\nCreate list of analyses" )
    cmd = [ "./listOfAnalyses.py", "-a", "-l" ]
    if A.ignore:
        cmd += [ "-i" ]
    exec ( cmd, A.dry_run )
    exec ( cmd + [ "-n" ], A.dry_run )
    if A.non_versioned:
        print ( "Update also the non-versioned files" )
        cmd = [ "./listOfAnalyses.py", "-l" ]
        if A.ignore:
            cmd += [ "-i" ]
        exec ( cmd, A.dry_run )
        exec ( cmd + [ "-n" ], A.dry_run )
    else:
        print ( "Update only versioned files" )

    ## SmsDictionary page
    gprint ( "\nCreate SmsDictionary" )
    cmd = [ "./smsDictionary.py", "-a" ]
    if A.feynman:
        cmd += [ "-f", "-c" ]
    exec ( cmd, A.dry_run )
    if A.non_versioned:
        exec ( [ "./smsDictionary.py" ], A.dry_run )

    if not A.no_pickle:
        print ( "\nCreate and publish database pickle" )
        exec ( [ "./publishDatabasePickle.py", "-b", "-f", db ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "-r", "-b", "-f", db ], A.dry_run )

    gprint ( "create Validation wiki" )
    cmd = [ "../validation/createWikiPage.py", "-c", ref_db ]
    if A.ignore:
        cmd += [ "-i" ]
    exec ( cmd + [ "-a", "-s", "-f" ], A.dry_run )
    exec ( cmd + [ "-a", "-u" ], A.dry_run )
    if A.non_versioned:
        exec ( cmd + [ "-s", "-f" ], A.dry_run )
        exec ( cmd + [ "-u" ], A.dry_run )
    if A.commit:
        gitPush( A.dry_run )

if __name__ == "__main__":
    main()

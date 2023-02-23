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

def gitPush( dry_run, commit ):
    """ git commit and git push 
    :param commit: commit message. if None, then do not commit
    """
    if commit == None:
        return
    cmd = f"cd ../../smodels.github.io/; git pull; git commit -am '{commit}'; git push"
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
    argparser.add_argument('-D', '--database', help='path to database  [../../smodels-database]', 
                    type=str, default="../../smodels-database" )
    argparser.add_argument('-R', '--reference_database', help='path to reference database  [../../smodels-database-release]', 
                    type=str, default="../../smodels-database-release" )
    argparser.add_argument ( '-c', '--commit', 
            help='git-commit and git-push to smodels.github.io (specify commit msg)',
            type=str, default = None )
    argparser.add_argument ( '-i', '--ignore', help='ignore the validation flags of analysis (i.e. also add non-validated results)', action='store_true' )
    A = argparser.parse_args()
    #db = "~/git/smodels-database/"
    db = A.database
    db = os.path.expanduser(db)
    if not os.path.exists(db):
        db = "~/tools/smodels-database/"
        db = os.path.expanduser(db)
    # ref_db = "~/git/smodels-database-release/"
    ref_db = A.reference_database
    ref_db = os.path.expanduser( ref_db )
    ## list of analyses, with and without superseded
    gprint ( "\nCreate ListOfAnalyses" )
    cmd = [ "./listOfAnalyses.py", "-a", "-l", "-d", db ]
    if A.ignore:
        cmd += [ "-i" ]
    exec ( cmd + [ "-f" ], A.dry_run )
    exec ( cmd + [ "-n" ], A.dry_run )
    if A.non_versioned:
        print ( "Update also the non-versioned files" )
        cmd = [ "./listOfAnalyses.py", "-l", "-d", db ]
        if A.ignore:
            cmd += [ "-i" ]
        exec ( cmd + [ "-f" ], A.dry_run )
        exec ( cmd + [ "-n" ], A.dry_run )
    else:
        print ( "Update only versioned files" )

    ## SmsDictionary page
    gprint ( "\nCreate SmsDictionary" )
    cmd = [ "./smsDictionary.py", "-a", "-d", db ]
    if A.feynman:
        cmd += [ "-f", "-c" ]
    exec ( cmd, A.dry_run )
    if A.non_versioned:
        exec ( [ "./smsDictionary.py", "-d", db ], A.dry_run )

    if not A.no_pickle:
        gprint ( "\nCreate and publish database pickle" )
        #exec ( [ "./publishDatabasePickle.py", "-b", "-f", db ], A.dry_run )
        #exec ( [ "./publishDatabasePickle.py", "-r", "-b", "-f", db ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "-a", "-p", "-s", "-r", "--full_llhds", "-b", "-f", db ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "-f", "./superseded.pcl" ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "-f", "./nonaggregated.pcl" ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "-f", "./full_llhds.pcl" ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "-F", "-f", "./fastlim.pcl" ], A.dry_run )
        exec ( [ "./publishDatabasePickle.py", "--txnamevalues", "-b", "-f", db ], A.dry_run )


    gprint ( "\nCreate Validation" )
    cmd = [ "../validation/createWikiPage.py", "-c", ref_db, "-d", db ]
    if A.ignore:
        cmd += [ "-i" ]
    exec ( cmd + [ "-a", "-s", "-f" ], A.dry_run )
    exec ( cmd + [ "-a", "--ugly" ], A.dry_run )
    if A.non_versioned:
        exec ( cmd + [ "-s", "-f" ], A.dry_run )
        exec ( cmd + [ "--ugly" ], A.dry_run )
    gitPush( A.dry_run, A.commit )

if __name__ == "__main__":
    main()

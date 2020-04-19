#!/usr/bin/env python3

"""
.. module:: compareValidations
   :synopsis: compare all the validations in two given database directories

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import glob, os, sys, copy, subprocess, colorama


def pprint ( *args ):
    f=open("comparison.log","at")
    print ( *args )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def error ( *args ):
    f=open("comparison.log","at")
    print ( colorama.Fore.RED, *args, colorama.Fore.RESET )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def info ( *args ):
    f=open("comparison.log","at")
    print ( colorama.Fore.GREEN, *args, colorama.Fore.RESET )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def warn ( *args ):
    f=open("comparison.log","at")
    print ( colorama.Fore.YELLOW, *args, colorama.Fore.RESET )
    f.write ( " ".join(map(str,args)) )
    f.write ( "\n" )
    f.close()

def getAnaTopo ( f ):
    """ retrieve the analysis id + topo from path name """
    ret = f.replace("/validation/","/")
    ret = ret.replace("13TeV/","").replace("8TeV/","")
    if ret.startswith("CMS/"):
        ret = ret[4:]
    else:
        ret = ret[6:]
    p = ret.find("_")
    ret = ret[:p]
    return ret

def compareDicts ( d1, d2 ):
    """ compare two dictionaries """
    for k,v1 in d1.items():
        if k == "t":
            continue
        v2 = d2[k]
        if v1 != v2:
            print ( "Dicts: %s != %s" % ( v1, v2 ) )
            return False
    return True

def compareDetails ( D1, D2, f ):
    lD1, lD2 = len(D1), len(D2)
    if lD1 != lD2:
        pprint ( "different number of validation points! %d versus %d" % ( lD1, lD2 ) )
        return False
    for d1,d2 in zip ( D1, D2 ):
        if not compareDicts ( d1, d2 ):
            error ( "%s != %s" % ( d1, d2 ) )
            return False
    return True

def compareValidation ( db1, db2, f ):
    pprint ( "compare validations %s" % getAnaTopo ( f ) )
    f1 = open ( db1 + f, "rt" )
    lines = f1.read()
    f1.close()
    if "<<< HEAD" in lines:
        error ( " ERROR: git conflict in %s%s" % ( db1, f ) )
        return False
    vd1 = eval ( lines.replace ( "validationData =", "" ) )
    f2 = open ( db2 + f, "rt" )
    lines = f2.read()
    f2.close()
    if "<<< HEAD" in lines:
        error ( " ERROR: git conflict in %s%s" % ( db2, f ) )
        return False
    vd2 = eval ( lines.replace ( "validationData =", "" ) )
    if vd1 == vd2:
        info ( "%s: exactly the same" % getAnaTopo ( f ) )
        return True
    else:
        warn ( "%s: differences. check details" % getAnaTopo ( f ) )
        return compareDetails ( vd1, vd2, f )

def compareDatabases ( db1, db2 ):
    print ( "compare databases: %s with %s" % ( db1, db2 ) )
    subprocess.getoutput ( "mv comparison.log comparison.old" )
    g1 = glob.glob ( "%s/*TeV/*/*/validation/T*.py" % db1 )
    g2 = glob.glob ( "%s/*TeV/*/*/validation/T*.py" % db2 )
    valFilesInBoth = set()
    valFilesMissing = set()
    for g in g1:
        gt = g.replace(db1,"")
        g_ = g.replace(db1,db2)
        if g_ in g2:
            valFilesInBoth.add ( gt )
        else:
            valFilesMissing.add ( g_ )
    for g in g2:
        gt = g.replace(db2,"")
        if gt in valFilesInBoth:
            continue
        valFilesMissing.add ( gt )
    print ( "%d validation files found in both databases." % ( len(valFilesInBoth) ) )
    print ( "%d validation files found missing in either database." % \
            ( len(valFilesMissing) ) )
    npassed,ntot=0,len(valFilesInBoth)
    for f in valFilesInBoth:
        res = compareValidation ( db1, db2, f )
        if res:
            npassed+=1
    print ( "%d/%d validation objects are ok" % ( npassed, ntot ) )

if __name__ == "__main__":
    db1 = "../../smodels-database/"
    db2 = "../../smodels-database-123/"
    compareDatabases ( db1, db2 )

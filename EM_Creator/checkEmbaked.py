#!/usr/bin/env python3

""" check .embaked files, look at double entries, etc """

import time

def check ( topo ):
    f=open("%s.embaked" % topo, "rt" )
    lines=f.readlines()
    f.close()
    allms = set()
    saved = {}
    comments = set()
    for ctr,line in enumerate(lines):
        if "#" in line:
            p = line.find("#" )
            comments.add ( line[p:] )
            line=line[:p]
        if line=="":
            continue
        if line[0]=="{":
            line = line[1:]
        line = line.strip()
        if line == "}":
            continue
        kv = line.split(":",1)
        masses = eval(kv[0])
        svs = kv[1]
        if svs.endswith(","):
            svs = svs[:-1]
        values = eval(svs)
        # print ( "l>%s,%s<" % (svs, type(values) ))
        if masses in allms:
            print ( "[checkEmbaked] mass vector %s appears twice!" % str(masses) )
            if not "__nevents__" in saved[masses]:
                print ( "[checkEmbaked] old version has no nevents. overwrite!" )
                saved[masses]=values
                continue
            if not "__nevents__" in values:
                print ( "[checkEmbaked] new version has no nevents. keep old!" )
                continue
            nold = saved[masses]["__nevents__"]
            nnew = values["__nevents__"]
            if nnew > nold:
                print ( "[checkEmbaked] newer version has more events. overwrite!" )
                saved[masses]=values
                continue
        else:
            saved[masses]=values
        allms.add ( masses )
    f=open("new%s.embaked" % topo, "wt" )
    for c in comments:
        f.write ( c )
    f.write ( "# rewritten %s\n" % time.asctime() )
    f.write ( "{" )
    for k,v in saved.items():
        f.write ( "%s: %s,\n" % ( str(k), str(v) ) )
    f.write ( "}\n" )
    f.close()

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description =
        'check embaked files, remove dupes')
    argparser.add_argument ('-t', '--topo',
        help = 'topo to look at',\
        type = str )
    args = argparser.parse_args()
    check ( args.topo )

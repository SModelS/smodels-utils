#!/usr/bin/env python3

""" simple script that compares two pickle files, see if there
    is any difference in the triangulation """

import pickle, os, argparse

def compareTriangulations ( o1, o2, label, tag, errors ):
    hasDifference=False
    o1.sort()
    o2.sort()
    for c,(i1,i2) in enumerate(zip(o1,o2)):
        if i1!=i2:
            hasDifference=True
            break
    if hasDifference:
        errors.append ( tag )
        if len(errors)<4:
            print ( f"difference in #{c} {label}: {tag}" )
        if len(errors)==4:
            print ( f"(omitting more such errors)" )
    else:
        pass
        # print ( f"no difference in {otag}" )
    # return errors

def compare ( pickle1 : os.PathLike, pickle2 : os.PathLike,
              interactive : bool = False ):
    """ compare the two pickle files, look only at the intersection of
        results """
    h1 = open ( pickle1, "rb" )
    dump1 = pickle.load ( h1 )
    h1.close()
    h2 = open ( pickle2, "rb" )
    dump2 = pickle.load ( h2 )
    h2.close()
    ## get the intersections
    osimplices1, osimplices2 = dump1["osimplices"], dump2["osimplices"]
    esimplices1, esimplices2 = dump1["esimplices"], dump2["esimplices"]
    opoints1, opoints2 = dump1["opoints"], dump2["opoints"]
    epoints1, epoints2 = dump1["epoints"], dump2["epoints"]
    otags = [ x for x in osimplices1.keys() if x in osimplices2.keys() ]
    etags = [ x for x in esimplices1.keys() if x in esimplices2.keys() ]
    errors = []
    for tag in otags:
        x1 = osimplices1[tag]
        x2 = osimplices2[tag]
        compareTriangulations ( x1, x2, "observed", tag, errors )
    for tag in etags:
        x1 = esimplices1[tag]
        x2 = esimplices2[tag]
        compareTriangulations ( x1, x2, "expected", tag, errors )
    if len(errors)>0:
        print ( f"the following {len(errors)} tags showed differences: {','.join(errors[:5])}" )
    else:
        print ( f"found no differences in triangulations" )
    if interactive:
        print ( "defined: otags, etags, osimplices1, osimplices2, esimplices1, esimplices2" )
        import IPython; IPython.embed( colors = "neutral" )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="compare two pickle files")
    ap.add_argument('-1', '--file1', help='pickle file 1 [official.pcl]',
            default='official.pcl')
    ap.add_argument('-2', '--file2', help='pickle file 2 [two.pcl]',
            default='two.pcl')
    ap.add_argument('-i', '--shell', help='start interactive shell at end',
            action="store_true" )
    args = ap.parse_args()
    compare ( args.file1, args.file2, args.shell )

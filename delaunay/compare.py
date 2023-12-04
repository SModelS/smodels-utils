#!/usr/bin/env python3

""" simple script that compares two pickle files, see if there
    is any difference in the triangulation """

import pickle, os, argparse

def compareTriangulations ( o1, o2, label, tag, errors ):
    hasDifference=False
    for i1,i2 in zip(o1,o2):
        if i1!=i2:
            hasDifference=True
            break
    if hasDifference:
        errors.append ( tag )
        if len(errors)<4:
            print ( f"difference in {label}: {tag}" )
        if len(errors)==4:
            print ( f"(omitting more such errors)" )
    else:
        pass
        # print ( f"no difference in {otag}" )
    # return errors

def compare ( pickle1 : os.PathLike, pickle2 : os.PathLike ):
    """ compare the two pickle files, look only at the intersection of
        results """
    h1 = open ( pickle1, "rb" )
    meta1, observed1, expected1 = ( pickle.load ( h1 ) for x in range(3) )
    h1.close()
    h2 = open ( pickle2, "rb" )
    meta2, observed2, expected2 = ( pickle.load ( h2 ) for x in range(3) )
    h2.close()
    ## get the intersections
    otags = [ x for x in observed1.keys() if x in observed2.keys() ]
    etags = [ x for x in expected1.keys() if x in expected2.keys() ]
    errors = []
    for tag in otags:
        x1 = observed1[tag]
        x2 = observed2[tag]
        compareTriangulations ( x1, x2, "observed", tag, errors )
    for tag in etags:
        x1 = expected1[tag]
        x2 = expected2[tag]
        compareTriangulations ( x1, x2, "expected", tag, errors )
    if len(errors)>0:
        print ( f"the following tags showed {len(errors)} differences: {','.join(errors[:5])}" )
    else:
        print ( f"found no differences in triangulations" )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="compare two pickle files")
    ap.add_argument('-1', '--file1', help='pickle file 1 [official.pcl]',
            default='official.pcl')
    ap.add_argument('-2', '--file2', help='pickle file 2 [two.pcl]',
            default='two.pcl')
    args = ap.parse_args()
    compare ( args.file1, args.file2 )

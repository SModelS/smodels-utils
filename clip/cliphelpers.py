#!/usr/bin/env python3

""" various helper functions around the clip cluster that do not fit in any of
the more specific modules """

def describeSet( inp ):
    """ describe a given set of indices in compact form.
    returns: a string
    """
    s = set()
    for i in inp:
        s.add(int(i))
    # return str( s )
    ret = ""
    firstIndex = s.pop() ## enter first element
    lastIndex = firstIndex
    for i in s:
        if i == lastIndex+1:
            lastIndex=i
        else:
            ret += "%d-%d, " % ( firstIndex, lastIndex )
            firstIndex = i
            lastIndex= i
    ret += "%d-%d" % ( firstIndex, lastIndex )
    return ret

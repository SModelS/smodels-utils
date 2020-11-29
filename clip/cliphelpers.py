#!/usr/bin/env python3

""" various helper functions around the clip cluster that do not fit in any of
the more specific modules """

def describeSet( s ):
    """ describe a given set of indices in compact form.
    returns: a string
    """
    # tmp = str(s)
    if type(s) in [ tuple, list ]:
        s = set(s)
    ret = ""
    firstIndex = s.pop() ## enter first element
    lastIndex = firstIndex
    for i in s:
        # print ( "i", i, "first", firstIndex, "last", lastIndex, i == lastIndex+1 )
        if i == lastIndex+1:
            lastIndex=i
        else:
            ret += "%d-%d, " % ( firstIndex, lastIndex )
            firstIndex = i
            lastIndex= i
    ret += "%d-%d" % ( firstIndex, lastIndex-1 )
    #if len(ret)>2:
    #    ret=ret[:-2]
    # return str( s )
    return ret

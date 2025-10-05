#!/usr/bin/env python3

def filterData ( data : list ):
    ret = []
    dropThese = [ "CMS-EXO-20-004", "ATLAS-EXOT-2018-06", \
                  "ATLAS-SUSY-2018-16-hino", "ATLAS-SUSY-2018-16", \
                  "ATLAS-SUSY-2018-42" ]
    dropThese.append ( "ATLAS-SUSY-2017-03" )
    dropThese.append ( "CMS-SUS-20-004" )
    outfile = "pvalues.png"
    for entry in data:
        if entry["id"] in dropThese:
            continue
        else:
            ret.append ( entry )
    return ret

def drawP( fudge : float = 0.5, 
           outfile : str = "pvalues.png" ):
    """ draw a histogram of the pvalues 
    :param fudge: draw for that fudge factor
    """
    with open("data.dict","rt") as f:
        data = eval(f.read())
    fudge = 0.5
    data = filterData ( data[fudge] )
    pvalues = [ x["p_norm"] for x in data ]
    from matplotlib import pyplot as plt
    plt.hist ( pvalues )
    plt.xlabel ( "p-values" )
    plt.ylabel ( "occurrence" )
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

if __name__ == "__main__":
    outfile = "pvalues.png"
    fudge = 0.5
    drawP( fudge, outfile )

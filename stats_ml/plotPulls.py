#!/usr/bin/env python3    

""" simple pulls plot from stats file """

def getValues():
    filename = "stats"
    with open ( filename, "rt" ) as f:
        d = eval(f.read())
    print ( d )
    ret = []
    for anaid, values in d.items():
        if not "p1" in values:
            continue
        # (estimated) sigma is predictedP1 minus predicted
        sigma = values["p1"]-values["center"]
        # delta is predicted minus truth
        delta = values["center"]-values["orig"]
        pull = delta / sigma
        ret.append ( pull )
    return ret

def plot():
    d = getValues()
    from matplotlib import pyplot as plt
    plt.hist ( d )
    outfile = "pulls.png"
    plt.savefig ( outfile )
    from smodels_utils.plotting.mpkitty import timg
    timg ( outfile )

if __name__ == "__main__":
    plot()

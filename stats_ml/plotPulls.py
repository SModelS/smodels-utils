#!/usr/bin/env python3    

""" simple pulls plot from stats file """

def getValues():
    filename = "stats"
    with open ( filename, "rt" ) as f:
        d = eval(f.read())
    ret = []
    for point, entry in d.items():
        for anaid, values in entry.items():
            pull = values["pull"]
            ret.append ( pull )
            print ( f"[{point:20d}] {anaid:10s}: {pull:.2f}" )
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

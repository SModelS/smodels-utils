#!/usr/bin/env python3

def main():
    import glob
    files = glob.glob("walker*log")
    steps = {}
    for f in files:
        nr = int ( f.replace("walker","").replace(".log","") )
        h = open ( f, "rt" )
        lines = h.readlines()
        h.close()
        for line in lines[::-1]:
            if "Step" in line:
                laststep = line[line.find("Step")+5:]
                for c in [ "/", ":", " has", " " ]:
                    if c in laststep:
                        laststep = laststep[:laststep.find(c)]
                laststep = int ( laststep.strip() )
                #print ( nr, laststep )
                steps[nr]=laststep
                break
    keys = list ( steps.keys() )
    keys.sort()
    tots = 0
    for k in keys:
        tots += steps[k]
        print ( k, steps[k] )
    print ( f"we have {len(keys)} entries, total of {tots} steps." )

main()

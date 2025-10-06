#!/usr/bin/env python3

def calc_T(p,bns):
    n_bns = len(bns) - 1
    pj = 1/n_bns
    size = len(p)
    counts = [0]*n_bns
    for i in p:
        for j in range(n_bns):
            if i>bns[j] and i<bns[j+1]:
                counts[j] += 1
    return sum(((i - size*pj)**2) / (size*pj) for i in counts)

def calc_Tabove(p,bns):
    n_bns = int((len(bns) - 1) / 2)
    pj = 1/n_bns
    p = [i for i in p if i>0.5]
    size = len(p)
    counts = [0]*n_bns
    for i in p:
        for j in range(int((len(bns)-1)/2),int(len(bns)-1)):
            tmp = j - int((len(bns)-1)/2)
            if i>bns[j] and i<bns[j+1]:
                counts[tmp] += 1
    return sum(((i - size*pj)**2) / (size*pj) for i in counts)

def drawT():
    with open("data.dict","rt") as f:
        data = eval(f.read())
    print ( data )

if __name__ == "__main__":
    drawT()

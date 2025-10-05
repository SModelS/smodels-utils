#!/usr/bin/env python3

def drawT():
    with open("data.dict","rt") as f:
        data = eval(f.read())
    print ( data )

if __name__ == "__main__":
    drawT()

#!/usr/bin/python

""" removes multiple identical xsection entries """

def correct ( In, Out=None ):
    f=open(In)
    lines=f.readlines()
    f.close()
    if Out==None: Out=In
    f=open(Out,"w")

    xsecLines=[]

    isInXSecBlock=False
    skipNextLine=False
    for line in lines:
        line=line.replace("/vienna","")
        if skipNextLine: ## are we in a second line of an xsec record?
            skipNextLine=False ## skip it!
            continue
        if line.find ("XSECTION")==0:
            isInXSecBlock=True # in xsec block?
            if line in xsecLines: ## do we have the line stored already?
                skipNextLine=True ## then skip this line and the next
                continue
        if not isInXSecBlock: ## not in xsec section? copy the lines!
            f.write ( line )
            continue
        ## we are in xsec block, and the line doesnt yet exist?
        ## write it! and remember it!
        f.write ( line )
        xsecLines.append ( line )

    f.close()

if __name__ == '__main__':
    import sys
    In="test.slha"
    for i in sys.argv[1:]: In=i
    correct ( In )


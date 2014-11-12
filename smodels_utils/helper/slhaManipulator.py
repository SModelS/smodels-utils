#!/usr/bin/python

"""
.. module:: slhaManipulator
        :synopsis: all sorts of manipulations of SLHA files.
                   FIXME we also want removal of dupes, 
                   keeping the last entry.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def removeXSecs ( In, Out=None ):
    """ 
        removes all XSECTION blocks 
        :params In: name of input filename
        :params Out: name of output filename. If None, In is overwritten.
        :params In: name of input filename

    """
    f=open(In)
    lines=f.readlines()
    f.close()
    if Out==None: Out=In
    f=open(Out,"w")
    inXSecBlock=False
    for (ctr,line) in enumerate(lines):
        if not inXSecBlock and line.find("XSECTION")==-1:
            f.write(line)
        if line.find("XSECTION")>-1:
            inXSecBlock=True
            continue
        if inXSecBlock==True:
            tokens=line.split()
            if len(tokens)==0:
                continue
            if tokens[0].isalpha():
                inXSecBlock=False
            continue
    f.close()

def removeDupes ( In, Out=None ):
    """ removes multiple identical xsection entries,
        always keeping the first entry.
        :params In: name of input filename
        :params Out: name of output filename. If None, In is overwritten.

    """
    f=open(In)
    lines=f.readlines()
    f.close()
    if Out==None: Out=In
    f=open(Out,"w")

    xsecLines=[]

    isInXSecBlock=False
    skipNextLine=False
    for line in lines:
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
    t=sys.argv[1:]
    if len(t)==0:
        t.append("test.slha")
    for i in t:
        ## removeDupes( i )
        removeXSecs( i )


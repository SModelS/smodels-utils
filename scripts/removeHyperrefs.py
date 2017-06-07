#!/usr/bin/python

""" This is a script that removes of most hyperrefs that are produced when converting rst files 
to .tex files. may come in handy when creating a document from our rst manual. 
Wolfgang Waltenberger
"""

## \hyperref[Tools:databasebrowser]{\emph{database browser}

import re
import commands
import IPython
import sys
import glob

def removeHref ( line ):
    n = re.sub ( '.href\{(.*)\}\{(.*)', r'\2', line )
    p=n.find("}")
    n=n[:p]+n[p+1:]
    # print "href: '%s' -> '%s'" % ( line.strip(), n.strip() )
    return n
    

def splitHyperrefs ( line ):
    if line.count ( "hyperref" ) < 2:
        return [ line ]
    lines = []
    pos = line.rfind("\hyperref")
    if pos < 0:
        return [ line ]
    l1 = line[:pos]
    l2 = line[pos:]
    for l in splitHyperrefs ( l1 ):
        lines.append ( l )
    for l in splitHyperrefs ( l2 ):
        lines.append ( l )
    return lines


def parse ( filename ):
    print "now treating",filename
    commands.getoutput ( "mv %s %s.old" % ( filename, filename ) )
    f=open ( filename+".old" )
    oldlines=f.readlines()
    f.close()
    lines=[]
    for l in oldlines:
        if not l.count ("hyperref" ) > 1:
            lines.append ( l )
        else:
            for l in splitHyperrefs ( l ):
                lines.append ( l )
        
    g=open ( filename, "w" )
    started_hyperref= False 
    for line in lines:
        n = line
        if started_hyperref:
            # print "started a hyperref: '%s'" % n.strip()
            n=n.replace("}}}","")
            started_hyperref = False
            g.write ( n )
            continue
        if not "hyperref" in line and not "href" in line:
            g.write ( line )
            continue
        #print "orig:",line.strip()
        if "href" in line:
            n = removeHref ( line )
            g.write ( n )
            continue
        if "hyperref" in n:
            m = re.search ( '.hyperref\[(.*)\]{.emph(.*)}}', n )
            n = re.sub ( '.hyperref\[(.*)\]{.emph{(.*)}}', r'\2', n )
            if m and len(m.groups())>1:
                g1=m.groups()[1]
                # print "groups",m.groups(),g1[1:-1]
                n=n.replace ( m.groups()[1], m.groups()[1][1:-1] )

            #n=n[1:-1]
            #if n!=line:
            #    n=n.replace ( "{\\emph{","" ).replace ( "}}", "" )
        m = re.search ( 'hyperref\[(.*)\]{(.*)', n )
        if False: ## m:
            m = re.search ( '.hyperref\[(.*)\]{.emph(.*)', n )
            n = re.sub ( '.hyperref\[(.*)\]{.emph(.*)', r'\2', n )
            #print "twoliners",m.groups()
            #print "n A =",n
            if m and len(m.groups())>1:
                g1=m.groups()[1]
                # print "groups",m.groups(),g1[1:-1]
                n=n.replace ( "{{", "" )
            #print "n B =",n
            #p=n.find("{")
            #n=n[:p]+n[p+1:]
            ##print ">>> more:",m.group(),m.groups() ## ,m.groupdict()
            started_hyperref=True
            ##IPython.embed()
            #sys.exit()
        #print "write:",n
        n = n.replace ( "emphdata set","emph{data set}" )
        g.write ( n )
    f.close()

# files = [ "installation.tex" ]
files = glob.iglob("*.tex")
for i in files:
    parse ( i )

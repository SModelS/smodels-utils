#!/usr/bin/env python3

import subprocess

for i in [ "T2tt", "T1tttt", "T5tctc", "T2bbWWoff", "T6bbWWoffSemiLep" ]:
    print ( i, end="... " )
    cmd = "tex2im -o %sO.png '\mathrm{%s}'" % ( i, i )
    subprocess.getoutput ( cmd )
    cmd = "convert %sO.png -rotate 270 %s.png" % ( i, i )
    subprocess.getoutput ( cmd )
    cmd = "scp %s.png smodels.hephy.at:/var/www/images/combination/" % (i)
    T=subprocess.getoutput ( cmd )
    print ( "done" )

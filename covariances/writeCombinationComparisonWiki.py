#!/usr/bin/env python3

""" simple script that writes the wiki page
http://smodels.hephy.at/wiki/CombinationComparisons  
"""

f=open("CombinationComparisons","w")

def header():
  f.write( """#acl +DeveloperGroup:read,write,revert -All:write,read Default
<<LockedPage()>>

= Comparison of combined upper limits, official versus SModelS =
""")


def footer():
  f.write ( "" )
  f.close()

def xsel():
  import subprocess
  cmd = "cat CombinationComparisons | xsel -i" 
  print ( cmd )
  subprocess.getoutput ( cmd )

def body():
  plots = { "16050": [ "T1tttt", "T2tt", "T5tctc" ], "16052": [ "T2bbWWoff", "T6bbWWoffSemiLep" ] }
  names = { "16050": "CMS-SUS-16-050", "16052": "CMS-PAS-SUS-16-052" }
  addBest=True
  columns = [ "Combined, aggregated", "Combined, full" ]
  if addBest:
  	columns.append ( "Best SR" )
  for name,topos in plots.items():
    f.write ( f"\n= {names[name]} =\n" )
    f.write ( "||<#EEEEEE:> '''Name''' " ) 
    for col in columns:
      f.write (f"||<#EEEEEE:> '''{col}''' " )
    f.write ( "||\n" )
    for topo in topos:
      url="http://smodels.hephy.at/images/combination/"
      f.write ( '|| {{%s%s.png}} || {{%sCMS%sagg_%s.png||width="500"}} || {{%sCMS%s_%s.png||width="500"}} ' % \
                ( url, topo, url, name, topo, url, name, topo ) )
      if addBest:
      	f.write ( '|| {{%sCMS%sbest_%s.png||width="500"}} ' % ( url, name, topo ) )
      f.write ( "||\n" )

def main():
  header()
  body()
  footer()
  xsel()

main()

"""
|| T1tttt || {{http://smodels.hephy.at/images/combination/CMS16050agg_T1tttt.png||width="500"}} || {{http://smodels.hephy.at/images/combination/CMS16050_T1tttt.png||width="500"}} ||
|| T2tt || {{http://smodels.hephy.at/images/combination/CMS16050agg_T2tt.png||width="500"}} || {{http://smodels.hephy.at/images/combination/CMS16050_T2tt.png||width="500"}} ||
|| T5tctc || {{http://smodels.hephy.at/images/combination/CMS16050agg_T5tctc.png||width="500"}} || {{http://smodels.hephy.at/images/combination/CMS16050_T5tctc.png||width="500"}}  ||

== CMS-PAS-SUS-16-052 ==

||<#EEEEEE:> '''Name''' ||<#EEEEEE:> '''Combined, aggregated''' ||<#EEEEEE:> '''Combined, full''' ||
|| T2bbWWoff || {{http://smodels.hephy.at/images/combination/CMS16052agg_T2bbWWoff.png||width="500"}} || {{http://smodels.hephy.at/images/combination/CMS16052_T2bbWWoff.png||width="500"}} ||
|| T6bbWWoffSemiLep || {{http://smodels.hephy.at/images/combination/CMS16052agg_T6bbWWoffSemiLep.png||width="500"}} || {{http://smodels.hephy.at/images/combination/CMS16052_T6bbWWoffSemiLep.png||width="500"}} ||

"""

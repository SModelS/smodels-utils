#!/usr/bin/python

import urllib2 as u
import set_path
import sys
from experiment import smsResults

exceptions=[
"SUS13003", #rpv
"SUS13010", #rpv
"SUS12027", #rpv
"SUSY_2013_03", #split-susy
"SUSY_2013_01", #long-lived charginos
"ATLAS_CONF_2013_092", #rpv
"ATLAS_CONF_2013_091", #rpv
"ATLAS_CONF_2013_058", #long-lived sleptons
"ATLAS_CONF_2013_026", #gmsb
"ATLAS_CONF_2012_153", #rpv
"ATLAS_CONF_2012_104", #msugra
"ATLAS_CONF_2012_103", #no ul numbers given
"ATLAS_CONF_2012_109", #no ul numbers given
"ATLAS_CONF_2012_152", #ggm
"ATLAS_CONF_2012_147", #gmsb
"ATLAS_CONF_2012_151", #no ul numbers given
"ATLAS_CONF_2012_145", #no ul numbers given
"ATLAS_CONF_2012_165", #no ul numbers given
"ATLAS_CONF_2013_068", #c tagging
"ATLAS_CONF_2014_001", #ggm
"ATLAS_CONF_2014_006", #no sms results
"SUS12015", #rpv
"SUS12018", #ggm
"SUS12023", #no ul numbers given, has been updated with more data
"SUS12016", #no ul numbers given, has been updated with more data
]

#find all ATLAS 8TeV results

print "Checking for ATLAS analyses\n "

req=u.Request("https://twiki.cern.ch/twiki/bin/view/AtlasPublic/SupersymmetryPublicResults")
response=u.urlopen(req)
text=response.read()
lines=text.split("\n")

i=1
bottom=None
while i<10:
  readtable=None
  for line in lines:
    if "table%s"%str(i) in line:
      readtable=True
      continue
    if "</table>" in line:
      readtable=None
      continue
    if readtable and '"twikiTableCol2"> 7 <' in line:
      bottom=True
      break
    if readtable and "twikiTableCol5" in line:
      if "CONFNOTE" in line:
        pas=line[line.find("CONFNOTE")+10:line.find("target")-2]
      elif "PAPERS" in line:
        pas=line[line.find("PAPERS")+7:line.find("target")-2]
      else: continue
      pas=pas.replace("-","_")
      if not smsResults.exists(pas, None) and not pas in exceptions: print "Analysis %s not in database" %pas
  if bottom: break
  i+=1

#find all CMS 8TeV results

print "\n "

print "Checking for CMS analyses\n "

req=u.Request("https://twiki.cern.ch/twiki/bin/view/CMSPublic/PhysicsResultsSUS")
response=u.urlopen(req)
text=response.read()
lines=text.split("\n")

i=2
bottom=None
while i<10:
  readtable=None
  for line in lines:
    if 'id="table%s"'%str(i) in line:
      readtable=True
      continue
    if "</table>" in line:
      readtable=None
      continue
    if readtable and 'SUS11' in line:
      bottom=True
      break
    if readtable and "twikiTableCol1" in line and "SUS1" in line:
      pas=line[line.find("SUS1"):line.find("SUS1")+8]
      if not smsResults.exists(pas, None) and not pas in exceptions: print "Analysis %s not in database" %pas
  if bottom: break
  i+=1


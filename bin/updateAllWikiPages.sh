#!/bin/sh

## a super simple script to update all wiki pages in a single go, 
## so that I only have to copy-and-paste.

./listOfAnalyses.py -a -p -n
./listOfAnalyses.py -a -p
./smsDictionary.py -a -p 

cd ../validation
./createWikiPage.py -c ~/git/branches/smodels-database -a -i -p
./createWikiPage.py -c ~/git/branches/smodels-database -a -p -u

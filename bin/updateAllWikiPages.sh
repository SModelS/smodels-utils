#!/bin/sh

## a super simple script to update all wiki pages in a single go.

## list of analyses, with and without superseded
./listOfAnalyses.py -a -n
./listOfAnalyses.py -a
./listOfAnalyses.py -n
./listOfAnalyses.py 
## SmsDictionary page
./smsDictionary.py -a 
./smsDictionary.py 
#./publishDatabasePickle.py -f ~/git/smodels-database/db31.pcl
#./publishDatabasePickle.py -r -f ~/git/smodels-database/db31.pcl
#./writeDatabaseWikiPage.py

cd ../validation
### validation page, official
./createWikiPage.py -c /home/walten/git/smodels-database-release -a -i -f
./createWikiPage.py -c /home/walten/git/smodels-database-release -i -f
### validation page, "ugly"
./createWikiPage.py -c /home/walten/git/smodels-database-release -a -u
./createWikiPage.py -c /home/walten/git/smodels-database-release -u

#!/bin/sh

## a super simple script to update all wiki pages in a single go, 
## so that I only have to copy-and-paste.

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

#cd ../validation
### validation page, official
#./createWikiPage.py -c /home/walten/git/branches/smodels-database -a -i -p -f
### validation page, "ugly"
#./createWikiPage.py -c /home/walten/git/branches/smodels-database -a -p -u
#
#VER=122
#echo "cat Databases | xsel -i"
#echo "cat ListOfAnalyses | xsel -i"
#echo "cat ListOfAnalysesWithSuperseded | xsel -i"
#echo "cat SmsDictionary | xsel -i"
#echo "cat ../validation/ValidationUgly${VER} | xsel -i"
#echo "cat ../validation/Validation${VER} | xsel -i"

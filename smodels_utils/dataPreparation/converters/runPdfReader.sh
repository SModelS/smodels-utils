#!/bin/sh

# wget https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2019-09/figaux_10b.pdf

./PDFAtlasReader.py -f figaux_10a.pdf -x "[150,850,50]" -y "[0,550,50]"

cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09-eff/orig/TChiWZacc0j.csv

./PDFAtlasReader.py -f figaux_10b.pdf -x "[150,850,50]" -y "[0,550,50]"

cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09-eff/orig/TChiWZeff0j.csv

./PDFAtlasReader.py -f figaux_10c.pdf -x "[150,850,50]" -y "[0,550,50]"

cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09-eff/orig/TChiWZaccnj.csv

./PDFAtlasReader.py -f figaux_10d.pdf -x "[150,850,50]" -y "[0,550,50]"

cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09-eff/orig/TChiWZeffnj.csv

#./PDFAtlasReader.py -f figaux_08a.pdf
#cp excl.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09/orig/TChiWZexcl.csv
#cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09/orig/TChiWZoul.csv
#
#./PDFAtlasReader.py -f figaux_08b.pdf
#
#cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09/orig/TChiWZeul.csv
#
#./PDFAtlasReader.py --xrange "[150,320,1]" --yrange "[0,160,1]" -f figaux_09a.pdf
#cp excl.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09/orig/TChiWHexcl.csv
#cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09/orig/TChiWHoul.csv
#
#./PDFAtlasReader.py --xrange "[150,320,1]" --yrange "[0,160,1]" -f figaux_09b.pdf
#
#cp ul.csv /home/walten/git/smodels-database/13TeV/ATLAS/ATLAS-SUSY-2019-09/orig/TChiWHeul.csv

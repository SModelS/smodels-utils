#!/bin/sh

URL=http://smodels.hephy.at/downloads/tarballs

for i in ma5_v1.4beta.tar MG5_aMC_v2.3.3.tar pythia-pgs.tgz; do
	echo $i;
	rm -f $i
	wget $URL/$i
done

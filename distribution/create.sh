#!/bin/sh

# a script that creates from scratch the tarball that we ship
# Wolfgang Waltenberger, december 2014

VERSION="1.0"

clearTarball()
{
  ## remove old tarball, just to be sure
	rm -rf smodels-v${VERSION}
	rm -rf smodels-v${VERSION}.tar.gz
}

createTarball()
{
	## create the tarball
	git clone -b public git@smodels.hephy.at:smodels smodels-v${VERSION}
	rm -rf smodels-v${VERSION}/.git 
	tar xvf database.tar
	mv testCopy smodels-v${VERSION}/smodels-database
	tar czvf smodels-v${VERSION}.tar.gz smodels-v${VERSION}
}

testTarball()
{
  ## explode the tarball and perform a simple test
	cp smodels-v${VERSION}.tar.gz /tmp/
	cd /tmp/
	tar xzvf smodels-v${VERSION}.tar.gz
	cd /tmp/smodels-v${VERSION}
	/tmp/smodels-v${VERSION}/runSModelS.py -f inputFiles/slha/simplyGluino.slha
}

clearTarball
createTarball
testTarball

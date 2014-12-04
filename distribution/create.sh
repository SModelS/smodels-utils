#!/bin/sh

# a script that creates from scratch the tarball that we ship
# Wolfgang Waltenberger, december 2014

VERSION="1.0beta"

clearTarball()
{
  ## remove old tarball, just to be sure
	rm -rf smodels-v${VERSION}
	rm -rf smodels-v${VERSION}.tgz
}

createTarball()
{
	## create the tarball
	git clone -b public git@smodels.hephy.at:smodels smodels-v${VERSION}
	rm -rf smodels-v${VERSION}/.git 
	tar czvf smodels-v${VERSION}.tgz smodels-v${VERSION}
}

testTarball()
{
  ## explode the tarball and perform a simple test
	cp smodels-v${VERSION}.tgz /tmp/
	cd /tmp/
	tar xzvf smodels-v${VERSION}.tgz
	cd /tmp/smodels-v${VERSION}
  sudo  python /tmp/smodels-v${VERSION}/setup.py install
	/tmp/smodels-v${VERSION}/runSModelS.py -f inputFiles/slha/simplyGluino.slha
}

clearTarball
createTarball
testTarball

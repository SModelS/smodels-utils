#!/bin/sh

# a script that creates from scratch the tarball that we ship
# Wolfgang Waltenberger, december 2014

getTarball()
{
	rm -rf smodels-vTMP
	git clone -b public git@smodels.hephy.at:smodels smodels-vTMP
	VERSION=`cat smodels-vTMP/version`
	export VERSION
	rm -rf smodels-v${VERSION}
	rm -rf smodels-v${VERSION}.tgz
	mv smodels-vTMP smodels-v${VERSION}
	rm -rf smodels-v${VERSION}/.git 
	tar czvf smodels-v${VERSION}.tgz smodels-v${VERSION}
}

getTarballFake()
{
  ## for testing purposes, a routine that pretends to fetch the tarball
	VERSION=`cat smodels-vTMP/version`
	export VERSION
	rm -rf smodels-v${VERSION}
	rm -rf smodels-v${VERSION}.tgz
	mv smodels-vTMP smodels-v${VERSION}
	rm -rf smodels-v${VERSION}/.git 
	tar czvf smodels-v${VERSION}.tgz smodels-v${VERSION}
}

testTarball()
{
	print "testing tarball"
  ## explode the tarball and perform a simple test
	cp smodels-v${VERSION}.tgz /tmp/
	cd /tmp/
	tar xzvf smodels-v${VERSION}.tgz
  # rm -r smodels-v${VERSION}
	cd /tmp/smodels-v${VERSION}
  sudo  python /tmp/smodels-v${VERSION}/setup.py install
	echo "now run runSModelS.py"
	/tmp/smodels-v${VERSION}/runSModelS.py -f inputFiles/slha/gluino_squarks.slha
	echo "now run Example.py"
  /tmp/smodels-v${VERSION}/Example.py -f inputFiles/slha/simplyGluino.slha  
}

getTarball
echo "Creating version $VERSION" 
testTarball

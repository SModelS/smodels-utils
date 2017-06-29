#!/bin/sh

## upload the code to pypi (WW)

REPO=pypitest
## REPO=pypi

rm -r dist/*
# python setup.py register -r $REPO
#python setup.py sdist upload -r $REPO
python setup.py sdist bdist_wheel
twine upload dist/* -r $REPO

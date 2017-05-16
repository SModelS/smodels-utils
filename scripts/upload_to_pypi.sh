#!/bin/sh

## upload the code to pypi (WW)

REPO=pypitest
## REPO=pypi

python setup.py register -r $REPO
python setup.py sdist upload -r $REPO

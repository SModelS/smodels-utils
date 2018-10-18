#!/bin/sh

## push gitolite repository to github (WW)

git clone --bare git@smodels.hephy.at:smodels
cd smodels.git
git push --mirror https://github.com/SModelS/smodels.git

#!/bin/sh

git clone --bare git@smodels.hephy.at:smodels-utils
cd smodels-utils.git
java -jar ~/bfg.jar -b 10M -D '*.tar' .
git reflog expire --expire=now --all && git gc --prune=now --aggressive
#git push --mirror https://github.com/SModelS/smodels-utils.git
git push --mirror git+ssh://git@github.com/SModelS/smodels-utils.git


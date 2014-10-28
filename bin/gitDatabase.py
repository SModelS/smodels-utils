#!/usr/bin/env python

import git
import setPath
from smodels.tools import rcFile
from smodels.experiment import smsHelpers

smsHelpers.base="/home/walten/git/smodels-database/"

print "base=",smsHelpers.base
repo=git.Repo ( smsHelpers.base )
print repo
print "branch name", repo.active_branch.name
print "branch path", repo.active_branch.path


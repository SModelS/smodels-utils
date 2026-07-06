#!/usr/bin/env python3

""" this is basically runSModelS but with an extra printer (yieldsPrinter)
"""

import sys
sys.path.insert(0,"../smodels-utils/")

from stats_ml import yieldsPrinter # yieldsPrinter is self-registering
from smodels.tools.runSModelS import main
main()

#!/bin/sh

../smodels_utils/plotting/rulerPlotter.py hiscore.slha -o paper/ruler.png
../smodels_utils/plotting/decayPlotter.py -f hiscore.slha -c -o paper/decays_color.png
../smodels_utils/plotting/decayPlotter.py -f hiscore.slha -c  -d -t  -o paper/decays.png

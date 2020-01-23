#!/usr/bin/env python3

import json
files = ['RegionA/BkgOnly.json', 'RegionB/BkgOnly.json', 'RegionC/BkgOnly.json']
for f in files:
    print(f)
    with open(f) as fi:
        bkg = json.load(fi)    
    for ch in bkg['channels']:
        print(ch['name'], len(ch['samples'][0]['data']))

#!/usr/bin/env bash

function cls_patch() {
  #1: model mass 1
  #2: model mass 2
  local mass1
  local mass2
  mass1="${1}"
  mass2="${2}"
  printf "\nmodel: %s, %s\n" "${mass1}" "${mass2}"
  pyhf cls \
  --backend pytorch \
  <(pyhf patchset apply BkgOnly.json patchset.json --name "ERJR_${mass1}p0_${mass2}p0")
}

# signal patchset for the SUSY 3L EW-ino analysis
if [[ ! -d 3L-likelihoods ]]; then
  curl -sL https://www.hepdata.net/record/resource/1404698?view=true | tar -xzv --one-top-level=3L-likelihoods
fi
cd 3L-likelihoods || exit

pyhf patchset verify BkgOnly.json patchset.json

cls_patch 250 150
cls_patch 300 150
cls_patch 450 150

cls_patch 100 60
cls_patch 500 300 

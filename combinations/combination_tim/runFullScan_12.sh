#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('pointsToRerunWithoutUnsensitiveAna/pointsToRerunWithoutUnsensitiveAna_mmg05_split12',15,'pointsToRerunWithoutUnsensitiveAna/outputFullScan_nlo_2p3_mmg05_split12')"
}

callmyprogram

echo $Done

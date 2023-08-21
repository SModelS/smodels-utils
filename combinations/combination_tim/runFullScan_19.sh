#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('pointsToRerunWithoutUnsensitiveAna/pointsToRerunWithoutUnsensitiveAna_mmg05_split19',30,'pointsToRerunWithoutUnsensitiveAna/outputFullScan_nlo_2p3_mmg05_split19')"
}

callmyprogram

echo $Done

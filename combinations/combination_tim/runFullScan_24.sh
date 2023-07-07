#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_24',23,'outputFullScan_nlo_2p3_mmg05_24')"
}

callmyprogram

echo $Done

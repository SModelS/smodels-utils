#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_27',23,'outputFullScan_nlo_2p3_mmg05_27')"
}

callmyprogram

echo $Done

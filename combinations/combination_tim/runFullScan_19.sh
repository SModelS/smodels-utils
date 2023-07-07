#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_19',25,'outputFullScan_nlo_2p3_mmg05_19')"
}

callmyprogram

echo $Done

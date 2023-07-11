#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo/2ndFilter_slha_nlo_far_r/2ndFilter_slha_nlo_far_r_27',23,'outputFullScan_nlo_2p3_mmg05_far_r_27')"
}

callmyprogram

echo $Done

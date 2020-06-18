#!/bin/sh

rm -f ratios.txt

./plotRatio.py -a1 ATLAS-SUSY-2016-07-orig -a2 ATLAS-SUSY-2016-07-eff -v1 T1_2EqMassAx_EqMassBy.py -v2 T1_2EqMassAx_EqMassBy.py -l1 "orig" -l2 "high stat" -o atlas_susy_2016_07_orig_vs_high_T1.png -c

./plotRatio.py -a1 ATLAS-SUSY-2016-07-orig -a2 ATLAS-SUSY-2016-07-eff -v1 T2_2EqMassAx_EqMassBy.py -v2 T2_2EqMassAx_EqMassBy.py -l1 "orig" -l2 "high stat" -o atlas_susy_2016_07_orig_vs_high_T2.png -c

./plotRatio.py -a1 ATLAS-SUSY-2016-07-old -a2 ATLAS-SUSY-2016-07-eff -v1 T1_2EqMassAx_EqMassBy.py -v2 T1_2EqMassAx_EqMassBy.py -l1 "low stat" -l2 "high stat" -o atlas_susy_2016_07_low_vs_high_T1.png -c

./plotRatio.py -a1 ATLAS-SUSY-2016-07-old -a2 ATLAS-SUSY-2016-07-eff -v1 T2_2EqMassAx_EqMassBy.py -v2 T2_2EqMassAx_EqMassBy.py -l1 "low stat" -l2 "high stat" -o atlas_susy_2016_07_low_vs_high_T2.png -c

./plotRatio.py -a1 ATLAS-SUSY-2016-07-orig -a2 ATLAS-SUSY-2016-07-old -v1 T1_2EqMassAx_EqMassBy.py -v2 T1_2EqMassAx_EqMassBy.py -l1 "orig" -l2 "low stat" -o atlas_susy_2016_07_orig_vs_low_T1.png -c

./plotRatio.py -a1 ATLAS-SUSY-2016-07-orig -a2 ATLAS-SUSY-2016-07-old -v1 T2_2EqMassAx_EqMassBy.py -v2 T2_2EqMassAx_EqMassBy.py -l1 "orig" -l2 "low stat" -o atlas_susy_2016_07_orig_vs_low_T2.png -c

./plotRatio.py -a1 ATLAS-SUSY-2016-07-orig -a2 ATLAS-SUSY-2016-07-eff -v1 T2_2EqMassAx_EqMassBy_2j_Meff_1600.py -v2 T2_2EqMassAx_EqMassBy_2j_Meff_1600.py -l1 "orig 2jMeff1600" -l2 "high stat 2jMeff1600" -o atlas_susy_2016_07_orig_vs_high_T2_2jMeff1600.png -c


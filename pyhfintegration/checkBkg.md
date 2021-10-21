# Consistency check between background numbers from json files and from the analysis paper

The numbers in the "full `JSON`" column are background numbers that were summed over all background contributions in the `JSON` file.  
In the "`dataInfo`" column the background numbers are taken from `dataInfo.expectedBG` for each SR, and those come from the analysis papers.

## ATLAS-SUSY-2018-31

SR     | full `JSON` | `dataInfo`
-------|-----------|---------
SRA_L  | 9.84      | 8.4
SRA_M  | 6.02      | 5.7
SRA_H  | 3.11      | 3.0
SRB    | 3.39      | 3.3
SRC_22 | 22.9      | 21.2
SRC_24 | 11.1      | 10.6
SRC_26 | 4.29      | 3.7
SRC_28 | 2.64      | 2.4

## ATLAS-SUSY-2018-14

SR   | full json | dataInfo
-----|-----------|---------
SRee | 0.460     | 0.46
SRmm | 0.109     | 0.11
SRem | 0.0070    | 0.007

These are from `Comb_bkgonly.json`. But `SRee_bkgonly.json` (`SRmm_bkgonly.json`) contains only one `channel` that has the same background as `Comb_bkgonly.json` in the 1st (2nd) `channel`.

N.B. : Here I mean `channel` in the sense of `JSON` channels.
## ATLAS-SUSY-2018-04

SR    | full json | dataInfo
------|-----------|---------
SRlow | 6.06      | 6.0
SRhig | 10.34     | 10.2

## ATLAS-SUSY-2019-08

SR             | full json | dataInfo
---------------|-----------|---------
SR_HM_Low_MCT  | 4.19      | 4.1
SR_HM_Med_MCT  | 2.90      | 2.9
SR_HM_High_MCT | 1.01      | 1.1
SR_MM_Low_MCT  | 5.38      | 4.6
SR_MM_Med_MCT  | 2.81      | 2.6
SR_MM_High_MCT | 1.39      | 1.4
SR_LM_Low_MCT  | 10.96     | 8.8
SR_LM_Med_MCT  | 10.32     | 11.3
SR_LM_High_MCT | 6.93      | 7.3

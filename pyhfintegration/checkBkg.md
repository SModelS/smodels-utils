# Consistency check between background numbers from json files and from the analysis paper

The numbers in the "full `JSON`" column are background numbers that were summed over all background contributions in the `JSON` file.  
In the "`dataInfo`" column the background numbers are taken from `dataInfo.expectedBG` for each SR, and those come from the analysis papers.

## ATLAS-SUSY-2018-31

SR     | full `JSON` |   `dataInfo`    | simplified `JSON`
-------|-----------|-------------------|-----------
SRA_L  | 9.84      | 8.4 &plusmn; 1.7  | 9.3 &plusmn; 1.2
SRA_M  | 6.02      | 5.7 &plusmn; 0.8  | 5.4 &plusmn; 0.8
SRA_H  | 3.11      | 3.0 &plusmn; 1.5  | 2.5 &plusmn; 0.8
SRB    | 3.39      | 3.3 &plusmn; 0.9  | 3.2 &plusmn; 0.8
SRC_22 | 22.9      | 21.2 &plusmn; 4.1 | 22.9 &plusmn; 2.4
SRC_24 | 11.1      | 10.6 &plusmn; 2.3 | 10.5 &plusmn; 1.6
SRC_26 | 4.29      | 3.7 &plusmn; 0.9  | 3.8 &plusmn; 0.8
SRC_28 | 2.64      | 2.4 &plusmn; 0.6  | 2.6 &plusmn; 0.5

## ATLAS-SUSY-2018-14

SR   | full json | dataInfo
-----|-----------|---------
SRee | 0.460     | 0.46
SRmm | 0.109     | 0.11
SRem | 0.0070    | 0.007

These are from `Comb_bkgonly.json`. But `SRee_bkgonly.json` (`SRmm_bkgonly.json`) contains only one `channel` that has the same background as `Comb_bkgonly.json` in the 1st (2nd) `channel`.

N.B. : Here I mean `channel` in the sense of `JSON` channels.
## ATLAS-SUSY-2018-04

SR    | full json |     dataInfo      | simplified json
------|-----------|-------------------|-----------
SRlow | 6.06      | 6.0 &plusmn; 1.7  | 7.3 &plusmn; 2.8
SRhig | 10.34     | 10.2 &plusmn; 3.3 | 8.7 &plusmn; 2

## ATLAS-SUSY-2019-08

SR             | full json |     dataInfo      | simplified json
---------------|-----------|-------------------|-----------
SR_HM_Low_MCT  | 4.19      | 4.1 &plusmn; 1.9  | 6.4 &plusmn; 2.0
SR_HM_Med_MCT  | 2.90      | 2.9 &plusmn; 1.3  | 4.6 &plusmn; 1.4
SR_HM_High_MCT | 1.01      | 1.1 &plusmn; 0.5  | 1.6 &plusmn; 0.6
SR_MM_Low_MCT  | 5.38      | 4.6 &plusmn; 1.7  | 3.8 &plusmn; 1.6
SR_MM_Med_MCT  | 2.81      | 2.6 &plusmn; 1.3  | 5.9 &plusmn; 2.0
SR_MM_High_MCT | 1.39      | 1.4 &plusmn; 0.6  | 1.8 &plusmn; 0.6
SR_LM_Low_MCT  | 10.96     | 8.8 &plusmn; 2.8  | 13.0 &plusmn; 2.6
SR_LM_Med_MCT  | 10.32     | 11.3 &plusmn; 3.1 | 9.8 &plusmn; 2.3
SR_LM_High_MCT | 6.93      | 7.3 &plusmn; 1.5  | 6.7 &plusmn; 1.5

## ATLAS-SUSY-2018-06


SR      | full json |     dataInfo      | simplified json
--------|-----------|-------------------|-----------
SR_low  | 53        | 46 &plusmn; 5     | 47 &plusmn; 4
SR_ISR  | 24.4      | 23.4 &plusmn; 2.1 | 24.4 &plusmn; 1.9

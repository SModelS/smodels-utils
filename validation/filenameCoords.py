# a file that contains the mapping of filenames to mass and width coordinate vectors
# e.g. THSCPM1b, a file in the slha/THSCPM1b.tar.gz validation tarball reads e.g.
# THSCPM1b_975_9.5e-19.slha, the axes are [[(x,w)],[(x,w)]]
# so the mass vector consists of item #1 (975) the widths vector consists of item #2 (9.5e-19)
coords = {}
coords["THSCPM1b"]={ "masses": [[1],[1]], "widths": [[2],[2]] }
coords["THSCPM2b"]={ "masses": [[1],[1]], "widths": [[2],[2]] }
coords["THSCPM3"]={ "masses": [[1,2],[1,2]], "widths": [[3],[3]] }
coords["THSCPM4"]={ "masses": [[1,2],[1,2]], "widths": [[3],[3]] }
#coords["THSCPM5"]={ "masses": [[1,2],[1,2]], "widths": [[4],[4]] }
coords["THSCPM8"]={ "masses": [[1,2],[1,2]], "widths": [[3],[3]] }
coords["T2Disp"]={ "masses": [[1,2],[1,2]], "widths": [[3],[3]] }
coords["T5Disp"]={ "masses": [[1,3],[1,3]], "widths": [[2],[2]] }
coords["TGQ"]={ "masses": [[1,2],[3,4]], "widths": None }
#coords["TDTM1F"]={ "masses": [[1,1],[1,1]], "widths": [[2],[2]] }
coords["TDTM2F"]={ "masses": [[1,3],[4]], "widths": [[2],[]] }
coords["TSelSelDisp"]={ "masses": [[1,3],[1,3]], "widths": [[2],[2]] }
coords["TSmuSmuDisp"]={ "masses": [[1,3],[1,3]], "widths": [[2],[2]] }
coords["TStauStauDisp"]={ "masses": [[1,3],[1,3]], "widths": [[2],[2]] }
coords["TRHadGM1"]={'masses': [[1], [3]], 'widths': [[2], [4]]}
#coords["TDTM1M2F"]={'masses': [[1, 3], [4, 6]], 'widths': [[2], [5]]}
coords["TDTM1M2F"]={'masses': [[1, 3], [4]], 'widths': [[2], []]}
coords["T1Disp"]={'masses': [[1, 3], [4, 6]], 'widths': [[2], [5]]}
coords["TChiZH"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChiWH"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChiWZoff"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChi_WinoBino_BRN2toZ50"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChi_WinoBino_BRN2toZ100"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChi_WinoBino_BRN2toH100"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChiWZ"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChi_HinoBino_BRN2Z100"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["TChi_HinoBino_BRN2Z50"]={'masses': [[1, 2], [3, 4]], 'widths': None}
coords["T5HG"]={'masses': [[1, 2, 3], [4, 5, 6]], 'widths': None}
coords["T5Hg"]={'masses': [[1, 2, 3], [4, 5, 6]], 'widths': None}

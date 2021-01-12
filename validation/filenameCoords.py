# a file that contains the mapping of filenames to mass and width coordinate vectors
# e.g. THSCPM1b, a file in the slha/THSCPM1b.tar.gz validation tarball reads e.g. 
# THSCPM1b_975_9.5e-19.slha, the axes are [[(x,w)],[(x,w)]]
# so the mass vector consists of item #1 (975) the widths vector consists of item #2 (9.5e-19)
coords = {}
coords["THSCPM1b"]={ "masses": [[1],[1]], "widths": [[2],[2]] }
coords["THSCPM1b"]={ "masses": [[1],[1]], "widths": [[2],[2]] }
coords["T2Disp"]={ "masses": [[1],[2]], "widths": [[3]] }
coords["T5Disp"]={ "masses": [[1],[3]], "widths": [[2]] }
coords["TGQ"]={ "masses": [[1,2],[3,4]], "widths": None }

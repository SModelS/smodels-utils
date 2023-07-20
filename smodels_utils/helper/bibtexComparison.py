#!/usr/bin/env python3

""" small script to compare two bibtex files """


def compare ( file1 : str, file2 : str ):
    """ compare bibtex file1 with bibtex file2
    """
    import bibtexparser, os, IPython
    file1 = os.path.expanduser ( file1 )
    file2 = os.path.expanduser ( file2 )
    h1 = open ( file1 )
    parse1 = bibtexparser.load ( h1 )
    h2 = open ( file2 )
    parse2 = bibtexparser.load ( h2 )
    e1 = parse1.entries
    e2 = parse2.entries
    h1.close()
    h2.close()
    d1, d2 = {}, {}
    for e in e1:
        if "label" in e:
            if e["label"] in d1:
                if e != d1[e["label"]]:
                    print ( f'{e["label"]} a second time -- and different -- in first!' )
            d1[ e["label"] ] = e
        else:
            print ( f'{e["ID"]} has no label in first!' )
    for e in e2:
        if "label" in e:
            d2[ e["label"] ] = e
        else:
            print ( f'{e["ID"]} has no label in second!' )
    e1.sort ( key = lambda x : x["label"] if "label" in x else x["ID"] )
    e2.sort ( key = lambda x : x["label"] if "label" in x else x["ID"] )
    for i,(x1,x2) in enumerate(zip(e1,e2)):
        labels= [ x1["ID"], x2["ID"] ]
        if "label" in x1:
            labels[0]= x1["label"]
        if "label" in x2:
            labels[1]= x2["label"]
        if x1==x2:
            print ( f"entry #{i} is good {labels[0]}" )
            continue
        print ( f"entry #{i} differs {labels}" )
    if True:
        IPython.embed( colors="neutral" )


if __name__ == "__main__":
    compare ( "~/git/smodels-database/database.bib", \
              "~/git/branches/smodels-database/database.bib" )

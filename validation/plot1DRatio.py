#!/usr/bin/env python3

"""
.. module:: plot1DRatio.py
   :synopsis: plots the ratio between two similar results, 1d, typically
              the ratio of the upper limit from the UL map, and the
              upper limit computed from combining the efficiency maps.
"""

#import logging
#logger = logging.getLogger(__name__)

from smodels_utils.helper.various import getValidationDataPathName
from validation.validationHelpers import getValidationFileContent
from smodels_utils.plotting import mpkitty as plt

def retrievePoints ( data : list )-> dict:
    """ given the data from the python validation dictionary, 
    retrieve points """
    points = {}
    for ctr,point in enumerate( data ):
        if not "axes" in point:
            noaxes+=1
            if noaxes < 5:
                f1 = imp1.__file__.replace(dbpath,"")
                slhapoint = point["slhafile"].replace(".slha","")
                print ( f"INFO: no axes in {f1}:{slhapoint}" )
            if noaxes == 5:
                print ( " ... (more error msgs like these) " )
            continue
        axes_ = point["axes"]
        if axes_ is None:
            continue
        if not "UL" in point:
            continue
        p={ "x": point["axes"]["x"], "UL": point["UL"], "signal": point["signal"]}
        if "eUL" in point:
            p["eUL"]=point["eUL"]
            p["er"]=point["signal"]/point["eUL"]
        r = point["signal"] / point["UL"]
        p["r"]=r
        points[point["axes"]["x"]] = p
    return points

def plot ( args : dict, points1 : list, points2 : list ):
    """ given all arguments, and the points: plot! """
    xlabel, ylabel = args["xlabel"], args["ylabel"]
    if xlabel in [  None, "" ]:
        xlabel = "x [GeV]"
    if ylabel in [  None, "" ]:
        ylabel = "ratio"
    x_list = list ( set( points1.keys() ).union ( set ( points2.keys() ) ) )
    x_list.sort()
    y_list = []
    ey_list = []
    for x in x_list:
        if x not in points1.keys() or x not in points2.keys():
            y_list.append ( float("nan") )
            ey_list.append ( float("nan") )
            continue
        y_list.append ( points2[x]["r"] / points1[x]["r"] )
        if not "er" in points1[x] or not "er" in points2[x]:
            ey_list.append ( float("nan") )
        else:
            ey_list.append ( points2[x]["er"] / points1[x]["er"] )

    plt.plot ( x_list, y_list, color="k", linestyle="-", label="observed" )
    plt.plot ( x_list, ey_list, color="k", linestyle="dotted", label="expected" )
    plt.xlabel ( xlabel )
    plt.ylabel ( ylabel )
    title = args["title"]
    if title == None:
        title = "ratio plot, XXXX"
    plt.title ( title )
    plt.legend()
    print ( args )
    filename = args["output"].replace("@a",args["analysis1"])
    filename = filename.replace("@t","")
    filename = filename.replace("@sr","")
    plt.savefig ( filename )

def draw ( args : dict ):
    """ draw, with arguments given as a dictionary """
    ipath1 = getValidationDataPathName ( args["dbpath"], args["analysis1"], 
            args["validationfile1"], args["folder1"] )
    content1 = getValidationFileContent ( ipath1 )
    ipath2 = getValidationDataPathName ( args["dbpath"], args["analysis2"], 
            args["validationfile2"], args["folder2"] )
    content2 = getValidationFileContent ( ipath2 )
    data1 = content1["data"]
    data2 = content2["data"]
    points1 = retrievePoints ( data1 )
    points2 = retrievePoints ( data2 )
    plot ( args, points1, points2 )
    if args["show"]:
        plt.kittyPlot()

def main():
    import argparse
    argparser = argparse.ArgumentParser( description = "1d ratio plot" )
    argparser.add_argument ( "-v1", "--validationfile1",
            help="first validation file [TChiHH_2EqMassAx_EqMassB1.py]",
            type=str, default="TChiHH_2EqMassAx_EqMassB1.py" )
    argparser.add_argument ( "-v2", "--validationfile2",
            help="second validation file. If empty, then same as v1. ['TChiHH_2EqMassAx_EqMassBy_combined.py']",
            type=str, default="TChiHH_2EqMassAx_EqMassBy_combined.py" )
    argparser.add_argument ( "-a1", "--analysis1",
            help="first analysis name, like the directory name [CMS-SUS-19-012]",
            type=str, default="CMS-SUS-19-012" )
    argparser.add_argument ( "-a2", "--analysis2",
            help="second analysis name, like the directory name, if not specified then same as analysis1 [CMS-SUS-19-012-eff]",
            type=str, default="CMS-SUS-19-012-eff" )
    argparser.add_argument ( "-l1", "--label1",
            help="label in the legend for analysis1, guess if None [None]",
            type=str, default=None )
    argparser.add_argument ( "-f1", "--folder1",
            help="validation folder name for analysis1 [validation]",
            type=str, default="validation" )
    argparser.add_argument ( "-f2", "--folder2",
            help="validation folder name for analysis2 [validation]",
            type=str, default="validation" )
    #argparser.add_argument ( "--SR",
    #        help="plot ratio of efficiencies of this signal region. None = bestSR. Will turn on --efficiencies [None]",
    #        type=str, default=None )
    argparser.add_argument ( "-o", "--output",
            help="outputfile, the @x's get replaced [ratios_@a_@t@sr.png]",
            type=str, default="ratios_@a_@t@sr.png" )
    argparser.add_argument ( "-l2", "--label2",
            help="label in the legend for analysis2, guess if None [None]",
            type=str, default=None )
    argparser.add_argument ( "-yl", "--ylabel",
            help="label on the y axis, guess if None",
            type=str, default=None )
    argparser.add_argument ( "-xl", "--xlabel",
            help="label on the x-axis, guess if None",
            type=str, default=None )
    argparser.add_argument ( "--title",
            help="plot title, guess if None",
            type=str, default=None )
    argparser.add_argument ( "-x", "--xmin",
            help="minimum x value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "-X", "--xmax",
            help="maximum x value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "-y", "--ymin",
            help="minimum y value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "-Y", "--ymax",
            help="maximum y value, None means auto [None]",
            type=float, default=None )
    argparser.add_argument ( "--comment",
            help="add a comment to the plot [None]",
            type=str, default=None )
    argparser.add_argument ( "-d", "--dbpath",
            help="path to database [../../smodels-database/]", type=str,
            default="../../smodels-database/" )
    argparser.add_argument ( "-e1", "--eul", action="store_true",
            help="for the first analysis, use expected, not observed, upper limits" )
    argparser.add_argument ( "-e2", "--eul2", action="store_true",
            help="for the second analysis, use expected, not observed, upper limits" )
    #argparser.add_argument ( "-e", "--efficiencies", action="store_true",
    #        help="plot ratios of efficencies of best SRs, not ULs" )
    #argparser.add_argument ( "-c", "--copy", action="store_true",
    #        help="cp to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    argparser.add_argument ( "-s", "--show", action="store_true",
            help="show plot in terminal" )
    #argparser.add_argument ( "-m", "--meta", action="store_true",
    #        help="produce the meta files, ratios.txt and ratioplots.md" )
    #argparser.add_argument ( "-p", "--push", action="store_true",
    #        help="commit and push to smodels.github.io, as it appears in https://smodels.github.io/plots/" )
    args = argparser.parse_args()

    #if args.SR != None:
    #    args.efficiencies = True
    if args.analysis2 in [ None, "", "None" ]:
        args.analysis2 = args.analysis1
    if not "_" in args.validationfile1:
        args.validationfile1 = args.validationfile1 + "_2EqMassAx_EqMassBy.py"
    if not args.validationfile1.endswith ( ".py" ):
        args.validationfile1 += ".py"

    draw ( vars(args) )

    """
    valfiles = [ args.validationfile1 ]
    for valfile1 in valfiles:
        valfile2 = args.validationfile2
        if valfile2 in [ "", "none", "None", None ]:
            valfile2 = valfile1
        if not "_" in valfile2:
            valfile2 = valfile2 + "_2EqMassAx_EqMassBy.py"
        draw ( args.dbpath, args.analysis1, valfile1, args.analysis2, valfile2,
               vars(args ) )

    if args.meta:
        writeMDPage( args.copy )

    cmd = "cd ~/git/smodels.github.io/; git commit -am 'automated commit'; git push"
    o = ""
    if args.push:
        print ( "[plotRatio] now performing %s: %s" % (cmd, o ) )
        o = subprocess.getoutput ( cmd )
    else:
        if args.copy:
            print ( "[plotRatio] now you could do:\n%s: %s" % (cmd, o ) )
    """

if __name__ == "__main__":
    main()

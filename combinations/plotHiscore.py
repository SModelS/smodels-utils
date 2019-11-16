#!/usr/bin/env python3

import pickle, os, sys, subprocess, time, fcntl
from protomodel import ProtoModel # RandomWalker
from smodels.tools.physicsUnits import GeV
sys.path.insert(0,"../" )
import smodels_utils.helper.sparticleNames
import smodels_utils.SModelSUtils
import smodels_utils.plotting.decayPlots
from smodels_utils.plotting import rulerPlotter, decayPlotter
import helpers

def setup():
    codedir = "/mnt/hephy/pheno/ww/git/"
    sys.path.insert(0,"%ssmodels/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/" % codedir )
    sys.path.insert(0,"%ssmodels-utils/combinations/" % codedir )
    if os.path.exists ( "./rundir.conf" ):
        with open ( "./rundir.conf" ) as f:
            rundir = f.read().strip()
            os.chdir ( rundir )
        return rundir
    return ""

def obtain ( number, picklefile ):
    """ obtain hiscore number <number> """
    if not os.path.exists ( picklefile ):
        print ( "[plotHiscore] hiscore.pcl does not exist. Trying to produce now with ./hiscore.py" )
        from argparse import Namespace
        args = Namespace()
        import hiscore
        hiscore.main ( *args )

    with open( picklefile,"rb" ) as f:
        #fcntl.flock( f, fcntl.LOCK_EX )
        hiscores = pickle.load ( f )
        trimmed = pickle.load ( f )
        #fcntl.flock( f, fcntl.LOCK_UN )
    if number < len(trimmed) and trimmed[number] is not None:
        Z = trimmed[number].Z
        print ( "[plotHiscore] obtaining trimmed protomodel #%d: Z=%.2f (%d particles)" % (number, Z, len ( trimmed[number].unFrozenParticles() ) ) )
        return trimmed[number],True
    Z = hiscores[number].Z
    print ( "[plotHiscore] obtaining untrimmed #%d: Z=%.2f" % (number, Z ) )
    return hiscores[ number ],False

def gitCommit ( dest, wanted ):
    """ if wanted, then git commit and git push to smodels.githuib.io """
    if not wanted:
        return False
    cmd = "cd %s ; git commit -am 'update'; git push " % dest
    print ( "[plotHiscore] now git-commit: %s" % cmd )
    out = subprocess.getoutput ( cmd )
    if out != "":
        print ( "[plotHiscore] %s" % out )
    return True

def discussPredictions ( protomodel ):
    print ( "How the Z comes about. Best combo:" )
    combo = protomodel.bestCombo
    for pred in combo:
        print ( "theory pred: %s:%s" % ( pred.expResult.globalInfo.id, ",".join ( map ( str, pred.txnames ) ) ) )
        # print ( "     `- ", pred.expResult.globalInfo.id, "ana", pred.analysis, "masses", pred.mass, "txnames", pred.txnames, "type", pred.dataType() )

def writeTex ( protomodel, keep_tex ):
    """ write the comment about ss multipliers and contributions, in tex 
    :param keep_tex: keep tex source of texdoc.png
    """
    ssm = {}
    for pids,v in protomodel.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        pname = helpers.toLatex ( pids, addSign = True )
        token = "%s = %.2f" % ( pname, v )
        if v in ssm.keys():
            v+=1e-10
        ssm[v] = token

    whatifs = ""
    if hasattr ( protomodel, "whatif" ):
        print ( "[plotHiscore] contributions-by-particle are defined" )
        #whatifs+="\\\\Contributions by particles: $"
        whatifs+="\\\\"
        whatifs+="Contributions by particles: $"
        totalcont = 0. ## to normalize contributions
        for k,v in protomodel.whatif.items():
            totalcont += (protomodel.Z - v)
        tok = {}
        for k,v in protomodel.whatif.items():
            if v in tok.keys():
                v+=1e-6
            tok[v] = "%s = %d%s" % ( helpers.toLatex(k), round(100.*(protomodel.Z - v)/totalcont ), "\%" )
        keys = list ( tok.keys() )
        keys.sort()
        for v in keys:
            whatifs+= tok[v] + ", "
        if len(keys)>0:
            whatifs = whatifs[:-2]
        #whatifs+= ", ".join ( tok )
        whatifs+="$"
    else:
        print ( "[plotHiscore] protomodel has no ``whatif'' defined (did you use an untrimmed protomodel?)" )

    import tex2png
    if len(ssm) == 0:
        ssm = { 0: "\\mathrm{none}" }
    sssm = ""
    keys = list ( ssm.keys() )
    keys.sort( reverse=True )
    # keys.sort( key = lambda x: abs(x-1.), reverse=True )
    nm= 7
    for k in keys[:nm]:
        # print ( "k", k, "v", ssm[k][:10] )
        sssm += ssm[k] + ", "
    if len(sssm)>2:
        sssm = sssm[:-2]
    src = "%d largest signal strength multipliers: $" % nm + sssm + "$" # + whatifs
    # src = "%d most extreme signal strength multipliers: $" % nm + sssm + "$" + whatifs
    # print ( "[plotHiscore] texdoc source in src=>>>>%s<<<<" % src )
    sssm = ""

    keys.sort( key = lambda x: abs(x-1.), reverse=True )
    for k in keys[:nm]:
        # print ( "k", k, "v", ssm[k][:10] )
        sssm += ssm[k] + ", "
    if len(sssm)>2:
        sssm = sssm[:-2]
    # src = "5 largest signal strength multipliers: $" + sssm + "$" + whatifs
    src += "\\\\"
    src += "\n%d smallest signal strength multipliers: $" % nm + sssm + "$" + whatifs
    if keep_tex:
        with open("texdoc.tex","wt") as f:
            f.write ( src+"\n" )
            f.close()
        print ( "[plotHiscore] wrote %s/texdoc.tex" % os.getcwd() )
    try:
        p = tex2png.Latex ( src, 600 ).write()
        f = open ( "texdoc.png", "wb" )
        f.write ( p[0] )
        f.close()
    except Exception as e:
        print ( "[plotHiscore] Exception when latexing: %s" % e )

def writeIndexHtml ( protomodel, gotTrimmed ):
    """ write the index.html file, see e.g.
        https://smodels.github.io/protomodels/
    :param gotTrimmed: is the model a trimmed model?
    :param keep_tex: keep tex files
    """
    ssm = []
    for k,v in protomodel.ssmultipliers.items():
        if abs(v-1.)<1e-3:
            continue
        ssm.append ( "%s: %.2f" % (helpers.getParticleName(k,addSign=True),v) )
    f=open("index.html","w")
    f.write ( "<html>\n" )
    f.write ( "<body>\n" )
    f.write ( "<center>\n" )
    f.write ( "<h1>Current best protomodel: Z=%.2f</h1>\n" % protomodel.Z )
    f.write ( "</center>\n" )
    dbver = "???"
    strategy = "aggressive"
    if hasattr ( protomodel, "dbversion" ):
        dbver = protomodel.dbversion
        dotlessv = dbver.replace(".","")
    trimmed="Untrimmed"
    if gotTrimmed:
        trimmed = "Trimmed"
    f.write ( "%s <b><a href=./hiscore.slha>ProtoModel</a> produced with <a href=https://smodels.github.io/docs/Validation%s>database v%s</a>, combination strategy <a href=./matrix_%s.png>%s</a> in step %d</b><br>\n" % \
            ( trimmed, dotlessv, dbver, strategy, strategy, protomodel.step ) )
    f.write ( "<table width=80%>\n<tr><td>\n" )
    if hasattr ( protomodel, "rvalues" ):
        rvalues=protomodel.rvalues
        rvalues.sort(key=lambda x: x[0],reverse=True )
        f.write ( "<br><b>%d predictions available. Highest r values are:</b><br><ul>\n" % len(rvalues) )
        for rv in rvalues[:5]:
            srv="N/A"
            if type(rv[1])==float:
                srv="%.2f" % rv[1]
            f.write ( "<li>%s:%s r=%.2f, r<sub>exp</sub>=%s<br>\n" % ( rv[2].analysisId(), ",".join ( map(str,rv[2].txnames) ), rv[0], srv ) )
        f.write("</ul>\n")
    else:
        print ( "[plotHiscore] protomodel has no r values!" )

    if hasattr ( protomodel, "contributions" ):
        print ( "[plotHiscore] contributions-per-analysis are defined" )
        f.write ( "<td><br><b>Contributions per analysis:</b><br>\n<ul>\n" )
        conts = []
        for k,v in protomodel.contributions.items():
            conts.append ( ( v, k ) )
        conts.sort( reverse=True )
        for v,k in conts:
            f.write ( "<li> %s: %s%s\n" % ( k, int(round(100.*v)), "%" ) )
        # f.write ( "</table>\n" )
    else:
        print ( "[plotHiscore] contributions are not defined" )

    height = 32*int((len(ssm)+3)/4)
    if ssm == []:
        height = 32
    if hasattr ( protomodel, "whatif" ):
        height += 32
    f.write ( "<td><img width=600px src=./texdoc.png>\n" ) #  % height )
    f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</table>" )
    f.write ( '<table style="width:80%">\n' )
    f.write ( "<td width=45%><img height=650px src=./ruler.png><td width=55%><img height=650px src=./decays.png>\n" )
    f.write ( "</table>\n" )
    # f.write ( "<br><font size=-1>Last updated: %s</font>\n" % time.asctime() )
    f.write ( "</body>\n" )
    f.write ( "</html>\n" )
    f.close()
    print ( "[plotHiscore] Wrote index.html" )

def copyFilesToGithub():
    files = [ "hiscore.slha", "index.html", "matrix_aggressive.png", "decays.png", 
              "ruler.png", "texdoc.png" ]
    for f in files:
        if not os.path.exists ( f ):
            continue
        O = subprocess.getoutput ( "cp %s ../../smodels.github.io/protomodels/" % f )
        if len(O)>0:
            print ( "[plotHiscore.py] when copying files: %s" % O )

def getPIDsOfTPred ( tpred, ret ):
    """ get the list of PIDs that the theory prediction should be assigned to """
    LSP = 1000022
    for pids in tpred.PIDs:
        for br in pids:
            for pid in br:
                if type(pid) in [ list ]:
                    for pp in pid:
                        apid = abs(pp)
                        if not apid in ret and not apid == LSP:
                            ret[apid]=set()
                        if not apid == LSP:
                            ret[apid].add ( tpred.analysisId() )
                else:
                    apid = abs(pid)
                    if not apid in ret and not apid == LSP:
                        ret[apid]=set()
                    if not apid == LSP:
                        ret[apid].add ( tpred.analysisId() )
    return ret

def plotRuler( protomodel ):
    resultsForPIDs = {}
    for tpred in protomodel.bestCombo:
        resultsForPIDs =  getPIDsOfTPred ( tpred, resultsForPIDs )
        # print ( "p", pidsofpred )
        # resultsForPIDs.union ( getPIDsOfTPred ( tpred ) )
    resultsFor = {}
    for pid,values in resultsForPIDs.items():
        resultsFor[ protomodel.masses[pid] ] = values

    print ( "[plotHiscore] now draw ruler.png" )
    rulerPlotter.draw ( protomodel.currentSLHA, "ruler.png", Range=(None,None),
                        mergesquark = False,
                        hasResultsFor = resultsFor )

def plotDecays ( protomodel ):
    print ( "[plotHiscore] now draw decays.png" )
    options = { "tex": True, "color": True, "dot": True, "squarks": True,
                "weakinos": True, "sleptons": True, "neato": True,
                "integratesquarks": False, "leptons": True }
    options["rmin"] = 0.
    ## FIXME add cross sections.
    decayPlotter.draw ( protomodel.currentSLHA, "decays.png", options,
                        ssmultipliers = protomodel.ssmultipliers )

def plot ( number, verbosity, picklefile, options ):
    ## plot hiscore number "number"
    protomodel, trimmed = obtain ( number, picklefile )
    # print ( "[plotHiscore] create slha file" )
    fname = protomodel.createSLHAFile ()
    subprocess.getoutput ( "cp %s hiscore.slha" % fname )
    opts = [ "ruler", "decays", "predictions", "copy", "html" ]
    for i in opts:
        if not i in options:
            options[i]=True

    plotruler = options["ruler"]
    if plotruler:
        plotRuler ( protomodel )
    plotdecays = options["decays"]
    if plotdecays:
        plotDecays ( protomodel )
    if options["predictions"]:
        discussPredictions ( protomodel )
    if options["html"]:
        writeTex ( protomodel, options["keep_tex"] )
        writeIndexHtml ( protomodel, trimmed )
    #if options["copy"]:
    #    copyFilesToGithub()

def main ():
    rundir = setup()
    import argparse
    argparser = argparse.ArgumentParser(
            description='hiscore proto-model plotter')
    argparser.add_argument ( '-n', '--number',
            help='which hiscore to plot [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--picklefile',
            help='pickle file to draw from [%shiscore.pcl]' % rundir,
            type=str, default="%shiscore.pcl" % rundir )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug, info, warn, err [info]',
            type=str, default="info" )
    argparser.add_argument ( '-H', '--nohtml',
            help='do not produce index.html',
            action="store_true" )
    argparser.add_argument ( '-R', '--noruler',
            help='do not produce ruler plot',
            action="store_true" )
    argparser.add_argument ( '-D', '--nodecays',
            help='do not produce decays plot',
            action="store_true" )
    argparser.add_argument ( '-p', '--predictions',
            help='list all predictions',
            action="store_true" )
    argparser.add_argument ( '-k', '--keep',
            help='keep latex files',
            action="store_true" )
    argparser.add_argument ( '-u', '--upload',
            help='upload to one of the following destinations: none, gpu, github, anomaly, interesting [none]. run --destinations to learn more', 
            type=str, default="" )
    argparser.add_argument ( '-c', '--commit',
            help='also commit and push to smodels.github.io (works only with -u github, anomaly, or interesting)',
            action="store_true" )
    argparser.add_argument ( "--destinations", 
            help="learn more about the upload destinations", action="store_true" )
    args = argparser.parse_args()
    if args.destinations:
        print ( "Upload destinations: " )
        print ( "      none: no upload" )
        print ( "       gpu: upload to GPU server, afs space." )
        print ( "            Result can be seen at http://www.hephy.at/user/wwaltenberger/protomodels/" )
        print ( "    github: upload to github git directory." ) 
        print ( "            Result can be seen at https://smodels.github.io/protomodels" )
        print ( "interesting: upload to github git directory, 'interesting' folder." )
        print ( "             Result can be seen at https://smodels.github.io/protomodels/interesting" )
        print ( "anomaly: upload to github git directory, 'anomaly' folder." )
        print ( "             Result can be seen at https://smodels.github.io/protomodels/anomaly" )
        return
    upload = args.upload.lower()
    if upload in [ "none", "" ]:
        upload = None

    options = { "ruler": not args.noruler, "decays": not args.nodecays,
                "predictions": args.predictions, "html": not args.nohtml,
                "keep_tex": args.keep }

    plot ( args.number, args.verbosity, args.picklefile, options )
    if upload is None:
        return
    F = "*.png hiscore.slha index.html"
    dest = ""
    destdir = "%s/git" % os.environ["HOME"]
    if upload == "github":
        dest = "%s/smodels.github.io/protomodels/" % destdir
    if upload in [ "interesting", "anomaly" ]:
        dest = "%s/smodels.github.io/protomodels/%s/" % ( destdir, upload )

    if dest != "":
        print ( "[plotHiscore] copying to %s" % dest )
        cmd = "cp %s %s" % ( F, dest )
        a = subprocess.getoutput ( cmd )
        if a != "":
            print ( "error: %s" % a )
            sys.exit()
        r = gitCommit( dest, args.commit )
        if not r:
            print ( "[plotHiscore] done. now please do yourself: " )
            print ( "cd %s" % dest )
            print ( "git commit -am 'update'" )
            print ( "git push" )
        return

    if upload == "gpu":
        import socket
        hostname = socket.gethostname()
        D = "/afs/hephy.at/user/w/wwaltenberger/www/protomodels"
        ## first the backup
        if "gpu" in hostname:
            ## make backup
            cmd = "cp %s/* %s/backup/" % ( D, D )
        else:
            cmd = "ssh hepgpu01.hephy.oeaw.ac.at cp %s/* %s/backup/" % ( D, D )
        print ( cmd )
        # now the new stuff
        O = subprocess.getoutput ( cmd )
        if len(O)>0:
            print ( "[plotHiscore.py] when uploading files: %s" % O )

        if "gpu" in hostname:
            ## make backup
            cmd = "cp %s/* %s/backup/" % ( D, D )
            subprocess.getoutput ( cmd )
            cmd = "cp %s %s" % (F, D )
        else:
            cmd = "scp %s hepgpu01.hephy.oeaw.ac.at:%s" % ( F, D )
        print ( cmd )
        O = subprocess.getoutput ( cmd )
        if len(O)>0:
            print ( "[plotHiscore.py] when uploading files: %s" % O )
        return
    print ( "error, dont know what to do with upload sink '%s'" % upload )

if __name__ == "__main__":
    main()

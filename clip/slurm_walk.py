#!/usr/bin/env python3

""" the tool with which to create and launch slurm jobs for the
protomodels walkers.
"""

import tempfile, argparse, stat, os, math, sys, time, glob, random
from smodels_utils.helper.terminalcolors import *
import subprocess
from typing import Union, List, Tuple

from ptools.sparticleNames import SParticleNames
namer = SParticleNames()

def remove( fname, keep):
    ## rmeove filename if exists
    if not os.path.exists ( fname ):
        return
    if keep:
        return
    try:
        if True:
            os.unlink ( fname )
    except:
        pass

basedir = f"/scratch-cbe/users/{os.environ['USER']}"
if "RUNDIR" in os.environ:
    basedir = os.environ["RUNDIR"].replace("/rundir","")
codedir = f"{basedir}/git"
if "CODEDIR" in os.environ:
    codedir = os.environ["CODEDIR"]
outputdir = f"{basedir}/outputs"
defaultrundir = f"{basedir}/rundir"

def mkdir ( Dir : str, symlinks : bool = True ):
    """ make a rundir directory. link typical tools

    :param symlink: create symlinks?
    """
    if not os.path.exists ( Dir ):
        o = os.mkdir ( Dir )
    os.chdir ( Dir )
    if not symlinks:
        return
    for k in [ "protomodels", "protomodels/ptools/hiscoreCLI.py",
        "protomodels/snippets/printSimpleHiscoreList.py",
        "protomodels/snippets/printSimpleHiscoreList.py",
        "protomodels/snippets/mergeTwoModels.py",
        "smodels-utils/clip/slurm_walk.py",
        "smodels-utils/clip/progressScanners.py" ]:
        bname = os.path.join ( basedir, os.path.basename ( k ) )
        if os.path.exists ( f"{codedir}/{k}" ) and not os.path.exists ( bname ):
            try:
                o = os.symlink ( f"{codedir}/{k}", bname )
            except FileExistsError as e:
                pass
    if Dir.endswith ( "/" ):
        Dir = Dir[:-1]
    bDir = os.path.basename(Dir)
    if not os.path.exists ( f'{os.environ["HOME"]}/{bDir}' ):
        o = os.symlink ( Dir, f'{os.environ["HOME"]}/{bDir}' )

def runOneJob ( pid : int, jmin : int, jmax : int, cont : str, dbpath : str,
    dry_run : bool, keep : bool, time : float, 
    cheatcode : Union[str,int], rundir : str,
    maxsteps : int, select : str, do_srcombine : bool, record_history : bool, 
    test_param_space : bool, run_mcmc: bool,
    seed : Union[None,int], update_hiscores : bool, stopTeleportationAfter : int,
    forbidden : List[int], wallpids : bool, templateSLHA : os.PathLike ):
    """ prepare everything for a single job
    :params pid: process id, integer that idenfies the process
    :param jmin: id of first walker
    :param jmax: id of last walker
    :param cont: pickle file to start with, "" means start from SM
    :param dbpath: path to database
    :param dry_run: dont act, just tell us what you would do
    :param keep: keep temporary files, for debugging
    :param time: time in hours
    :param cheatcode: in case we wish to start with a cheat model
    :param rundir: the run directory
    :param maxsteps: max number of steps
    :param select: select for certain results, e.g. "all", "ul", "em",
                   "txnames:T1,T2"
    :param do_srcombine: if true, then also perform combinations, either via
                        simplified likelihoods or via pyhf
    :param record_history: if true, turn on the history recorder
    :param test_param_space: If True, walk over the param space keeping constant K and TL
    :param run_mcmc: if true, run mcmc walk without changing dimensions
    :param seed: the random seed for the walker
    :param update_hiscores: update the hiscores at the end
    :param stopTeleportationAfter: stop teleportation after this step.
           if -1, dont run teleportation at all.
    :param forbidden: any forbidden pids we dont touch
    :param templateSLHA: name of the templateSLHA file
    """ 
    if not "/" in dbpath and not dbpath in [ "official" ]: ## then assume its meant to be in rundir
        dbpath = f"{rundir}/{dbpath}"
    line = f"run walkers {jmin} - {jmax-1}"
    if jmax == jmin:
        jmax = jmin + 1
    if jmax == jmin + 1:
        line = f"run walker {jmin}"
    slurmdir = f"{rundir}/slurm/" 
    if not os.path.exists ( slurmdir ):
        os.mkdir ( slurmdir )
    runner = f"{slurmdir}/RUNNER_{jmin}.py"
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import os, sys\n" )
        f.write ( f"sys.path.insert(0,'{codedir}/smodels-utils/')\n" )
        f.write ( f"sys.path.insert(0,'{codedir}/protomodels')\n" )
        f.write ( f"os.chdir('{rundir}')\n" )
        if not wallpids:
            f.write ( "## offshell run below ATLAS-SUSY-2019-09 threshold!\n" )
            f.write ( "from builder.manipulator import Manipulator\n" )
            f.write ( "Manipulator.walledpids[1000024]=30\n" )
        f.write ( "from walker import factoryOfWalkers\n" )
        scheatcode=f"'{cheatcode}'"
        try:
            cheatcode = int(cheatcode)
            scheatcode = f"{cheatcode}"
        except ValueError as e:
            pass
        f.write ( f"factoryOfWalkers.createWalkers ( {jmin}, {jmax}, '{cont}', dbpath='{dbpath}', cheatcode={scheatcode},\n" )
        f.write ( f"    rundir='{rundir}', maxsteps={maxsteps},\n" )
        f.write ( f"    seed={seed}, select='{select}', do_srcombine={do_srcombine}, test_param_space = {test_param_space}, run_mcmc = {run_mcmc},\n" )
        f.write ( f"    record_history={record_history}, update_hiscores={update_hiscores}, stopTeleportationAfter={stopTeleportationAfter},\n" )
        f.write ( f"    forbiddenparticles={forbidden},\n" )
        f.write ( f"    templateSLHA='{templateSLHA}'\n" )
        f.write ( ")\n" )
    os.chmod( runner, 0o755 ) # 1877 is 0o755
    # Dir = getDirname ( rundir )

    ram = max ( 10000., 4000. * ( jmax - jmin ) )
    ram = ram*1.5
    if "comb" in rundir: ## combinations need more RAM
        ram = ram * 1.2
    if "history" in rundir: ## history runs need more RAM
        ram = ram * 1.3
    if update_hiscores: ## make sure we have a bit more for that
        ram = ram * 1.2
    ram=int(ram)
    proxies = glob.glob ( f"{rundir}/proxy*pcl" )
    if len(proxies)>0:
        ram = ram *.8
    # cmd = [ "srun" ]
    cmd = [ "sbatch" ]
    cmd += [ "--error", f"{outputdir}/walk-%j.out",
             "--output", f"{outputdir}/walk-%j.out" ]
    cmd += ["--cpus-per-task", "3"]
    
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd += [ "--qos", qos ]
    # cmd += [ "-n", str(jmax - jmin) ]
    # cmd += [ "--threads-per-core", str(jmax - jmin) ]
    # cmd += [ "-N", str(jmax - jmin) ]
    # cmd += [ "-k" ]
    cmd += [ "--mem", f"{ram:d}M", "--time", f"{time*60-1}", runner ]
    scmd =  " ".join ( cmd )
    scmd = scmd.replace ( basedir, "$BASE" )
    if dry_run:
        print ( "[slurm.py] dry_running:", scmd )
    else:
        print ( "[slurm.py] running", scmd )
        a=subprocess.run ( cmd, capture_output=True )
        sa = str(a)
        sb = str ( a.stdout.decode().strip() )
        if "Submitted batch job " in sb:
            sb=sb.replace("Submitted batch job ",f"Submitted batch job {YELLOW}" )
            sb+=RESET
        print ( sb )
        if not "returncode=0" in sa:
            sa = f"{RED}{sa}{RESET}"
        print ( f"returned: {sa}" )
        # time.sleep( random.uniform ( 0., 1. ) )

def produceLLHDScanScript ( pid1 : int, yvariable : Union[int,tuple], force_rewrite : bool,
        rundir : str, nprocs : int, select : str, do_srcombine : bool,
        uploadTo : str ) -> str:
    """
    produces the llhdscanner<pid>.sh scripts

    :returns: filename of script
    """
    fname = f"{rundir}/L{namer.asciiName(pid1)}.sh"
    if yvariable == -1:
        yvariable = 1000022
    if yvariable != 1000022:
        yvn = namer.asciiName(yvariable).replace(" ","").replace(",","")
        yvn = yvn.replace("~","m")
        fname = f"{rundir}/L{namer.asciiName(pid1)}_{yvn}.sh"
    sselect,sdo_srcombine = "",""
    if select != "":
        sselect = f" --select '{select}'"
    if do_srcombine:
        sdo_srcombine = f" --do_srcombine"
    if force_rewrite or not os.path.exists ( fname ):
        with open ( fname, "wt" ) as f:
            f.write ("#!/bin/sh\n\n"  )
            f.write ( f"{codedir}/protomodels/ptools/llhdScanner.py -R {rundir} --draw --xvariable {pid1} --yvariable '{yvariable}' --uploadTo {uploadTo} --nproc {nprocs}{sselect}{sdo_srcombine}\n" )
            f.close()
        os.chmod ( fname, 0o775 )
    return fname

def produceScanScript ( pid : int, force_rewrite : bool, yvariable : int,
        rundir : str , nprocs : int, dbpath : str, select : str,
        do_srcombine : bool, uploadTo : str ) -> str:
    """ produce the script to scan for the test statistics

    :returns: filename of script
    """
    syvariable=""
    if yvariable not in [ -1, "-1" ]:
        syvariable=namer.asciiName(yvariable)
        #syvariable=str(yvariable)
    fname = f"{rundir}/M{namer.asciiName(pid)}{syvariable}.sh"
    if force_rewrite or not os.path.exists ( fname ):
        argyvariable=""
        if yvariable!=0:
            argyvariable = f" --pid2 {yvariable}"
        with open ( fname, "wt" ) as f:
            f.write ("#!/bin/sh\n\n"  )
            cmd = f"{codedir}/protomodels/ptools/teststatScanner.py"
            args = f"--nproc {nprocs} -R {rundir} -r -d -c -P -p {pid} {argyvariable}"
            args += f" --dbpath '{dbpath}'"
            args += f" --select '{select}'"
            args += f" --uploadTo '{uploadTo}'"
            if do_srcombine:
                args += " --do_srcombine"
            f.write ( f"{cmd} {args}\n" )
            f.close()
        os.chmod ( fname, 0o775 )
    return fname

def fetchUnfrozenFromDict( rundir, includeLSP = True ):
    """ fetch pids of unfrozenparticles from dictionary
        in <rundir>/pmodel.py, if exists.
    :param includeLSP: if False, do not include the LSP in list
    :returns: list of pids, or None.
    """
    fname = f"{rundir}/states.dict"
    if not os.path.exists ( fname ):
        print ( f"[slurm.py] could not find {fname} file when trying to fetch unfrozen pids" )
        return None
    with open ( fname, "rt" ) as f:
        lines = f.read()
    lines = lines.replace("nan","'nan'" )
    D = eval( lines )
    M = D[0]["masses"]
    ret = []
    for k,v in M.items():
        if not includeLSP and k == 1000022:
            continue
        if v < 90000:
            ret.append(k)
    return ret

def fetchUnfrozenSSMsFromDict( rundir ):
    """ fetch pid pairs of ssmultipliers from dictionary
        in <rundir>/states.dict, if exists.
    :returns: list of pid pairs, or None.
    """
    ## FIXME the pid pairs should be taken from hiscore file, so we have xsecs to look at!
    print ( "[slurm.py:fetchUnfrozenSSMsFromDict] FIXME can we find out which productions we can ignore?" )
    # fname = f"{rundir}/pmodel.py"
    fname = f"{rundir}/states.dict"
    if not os.path.exists ( fname ):
        print ( f"[slurm.py] could not find {fname} file when trying to fetch unfrozen ssms" )
        return None
    with open ( fname, "rt" ) as f:
        lines = f.read()
    lines = lines.replace("nan","'nan'" )
    D = eval( lines )
    M = D[0]["masses"]
    ssms = D[0]["ssmultipliers"]
    pids = []
    for k,v in M.items():
        if v < 90000:
            pids.append(k)
    ret = []
    for ssmpids,ssm in ssms.items():
        takeIt = True
        hasStop = False
        hasSquark = False
        for ssmpid in ssmpids:
            #if abs(ssmpid) == 1000022:
            #    continue
            if abs(ssmpid) in [ 1000006, 2000006 ]:
                hasStop = True
            if abs(ssmpid) in [ 1000001, 1000002, 1000003, 1000004 ]:
                hasSquark = True
            if abs(ssmpid) not in pids:
                takeIt = False
        if hasStop and hasSquark:
            takeIt = False
        if 1000022 in ssmpids or -1000022 in ssmpids:
            print ( "[slurm.py] in this iteration we ignore LSP production modes!" )
            takeIt = False
        if takeIt:
            ret.append ( ssmpids )
    return ret

def runLLHDScanner( pid : int, yvariable : Union[Tuple,int] , dry_run : bool,
        time : float, rewrite : bool, rundir : str, select : str,
        do_srcombine : bool, uploadTo : str ):
    """ run the llhd scanner for pid, on the current hiscore
    :param pid: pid of particle on x axis. if zero, run all unfrozen pids of hiscore
    :param dry_run: do not execute, just say what you do
    :param rewrite: force rewrite of scan script
    """
    if pid == 0:
        pids = fetchUnfrozenFromDict( rundir, includeLSP = False )
        if pids == None:
            pids = [ 1000001, 1000003, 1000006 ]
        for i in pids:
            runLLHDScanner ( i, yvariable, dry_run, time, rewrite, rundir, select,
                             do_srcombine, uploadTo )
        return
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd = [ "sbatch" ]
    cmd += [ "--error", f"{outputdir}/llhd-%j.out",
             "--output", f"{outputdir}/llhd-%j.out" ]
    # cmd = [ "srun" ]
    cmd += [ "--qos", qos ]
    cmd += [ "--mem", "8G" ]
    cmd += [ "-c", "10" ]
    #cmd += [ "--ntasks-per-node", "5" ]
    # cmd += [ "--pty", "bash" ]
    cmd += [ "--time", f"{time * 60 - 1}" ]
    nprcs = 2 # was at 10
    script = produceLLHDScanScript ( pid, yvariable, rewrite, rundir, nprcs,
            select, do_srcombine, uploadTo  )
    cmd += [ script ]
    print ( "[runLLHDScanner]", " ".join ( cmd ) )
    if dry_run:
        return
    a = subprocess.run ( cmd )
    print ( ">>", a )

def runScanner( pid : Union[str,int], dry_run : bool, time : float, rewrite : bool,
        yvariable : Union[str,int], rundir : str, dbpath : str, select : str,
        do_srcombine : bool, uploadTo : str ):
    """ run the teststat scanner for pid, on the current hiscore
    :param pid: if 0, run on unfrozen particles in hiscore.
    :param dry_run: do not execute, just say what you do
    :param rewrite: force rewrite of scan script
    :param yvariable: if >0, scan for ss multipliers (pid,yvariable),
                 if 0, scan all ss multipliers, if < 0, scan masses,
                 not ssm multipliers.
    """
    pid = namer.pid ( pid )
    yvariable = namer.pid ( yvariable )
    if pid == 0:
        if yvariable == 0:
            pidpairs = fetchUnfrozenSSMsFromDict( rundir )
            for pidpair in pidpairs:
                runScanner ( pidpair[0], dry_run, time, rewrite, pidpair[1], rundir,
                             dbpath, select, do_srcombine, uploadTo )
            return
        pids = fetchUnfrozenFromDict( rundir )
        if pids == None:
            pids = [ 1000001, 1000003, 1000006, 1000022 ]
        for i in pids:
            runScanner ( i, dry_run, time, rewrite, yvariable, rundir, dbpath, select,
                         do_srcombine, uploadTo )
        return
    qos = "c_short"
    if time > 48:
        qos = "c_long"
    if 8 < time <= 48:
        qos = "c_medium"
    cmd = [ "sbatch" ]
    cmd += [ "--error", f"{outputdir}/scan-%j.out",
             "--output", f"{outputdir}/scan-%j.out" ]
    # cmd = [ "srun" ]
    cmd += [ "--qos", qos ]
    cmd += [ "--mem", "10G" ]
    cmd += [ "-c", f"8" ]
    # cmd += [ "--ntasks-per-node", "5" ]
    # cmd += [ "--pty", "bash" ]
    cmd += [ "--time", f"{time * 60 - 1}" ]
    nprc = 2
    fname = produceScanScript ( pid, rewrite, yvariable, rundir, nprc, dbpath, select,
                                do_srcombine, uploadTo )
    cmd += [ fname ]
    print ( f"[runScanner] {' '.join ( cmd )}" )
    if dry_run:
        return
    a=subprocess.run ( cmd, capture_output=True )
    sa = str(a)
    sb = str ( a.stdout.decode().strip() )
    if "Submitted batch job " in sb:
        sb=sb.replace("Submitted batch job ",f"Submitted batch job {YELLOW}" )
        sb+=RESET
    print ( sb )
    if not "returncode=0" in sa:
        sa = f"{RED}{sa}{RESET}"
    print ( f"returned: {sa}" )

def getDirname ( rundir ):
    """ get the directory name of rundir, e.g.:
        /{basedir}/rundir.fake1 -> fake1
    """
    ret = rundir
    if ret.endswith("/"):
         ret = ret[:-1]
    p = ret.rfind("/")
    if p>-1:
         ret = ret[p+1:]
    ret = ret.replace("rundir.","")
    return ret

def runUpdater( dry_run : bool, time : float, rundir : os.PathLike,
        maxiterations : Union[None,int], dbpath : str, uploadTo : str ):
    """ thats the hiscore updater
    :param dry_run: create the scripts, dont start them
    :param time: time, given in minutes(?)
    :param maxiterations: maximum number of iterations to run the updater
    :param dbpath: database path, @rundir@ will get replaced by rundir
    :param uploadTo: directory under smodels.github.io/protomodels to upload to
    """

    runner = f"{rundir}/upHi.py"
    if maxiterations == None:
        maxiterations = 1000
    #rd=rundir[rundir.find("rundir")+7:]
    # uploadTo=f"2020_PioneerStudy/{rd}"
    #while rd.endswith("/"):
    #    rd=rd[:-1]
    with open ( runner, "wt" ) as f:
        f.write ( "#!/usr/bin/env python3\n\n" )
        f.write ( "import os, sys\n" )
        f.write ( f"sys.path.insert(0,'{codedir}')\n" )
        f.write ( f"sys.path.insert(0,'{codedir}/protomodels')\n" )
        f.write ( f"sys.path.insert(0,'{codedir}/protomodels/ptools')\n" )
        f.write ( f"rundir='{rundir}'\n" )
        f.write ( f"os.chdir(rundir)\n" )
        f.write ( "from ptools import updateHiscores\n" )
        f.write ( 'batchjob="SLURM_JOBID" in os.environ\n' )
        f.write ( f'did_srcombine=updateHiscores.didSRCombine ( rundir )\n' )
        f.write ( f"updateHiscores.loop ( rundir=rundir, maxruns={maxiterations}, createPlots=not batchjob,\n" )
        f.write ( f"    uploadTo='{uploadTo}', do_srcombine=did_srcombine, dbpath='{dbpath}' )\n" )
    os.chmod( runner, 0o755 ) # 1877 is 0o755
    cmd = [ "sbatch", "--mem", "25G" ]
    if maxiterations > 5:
        cmd = [ "srun", "--mem", "25G" ]
        cmd += [ "--reservation", "interactive" ]
    cmd += [ "--error", f"{outputdir}/hi-%j.out",
             "--output", f"{outputdir}/hi-%j.out" ]
    cmd += [ "--time", f"{time * 60 - 1}" ]
    qos = "c_short"
    if time > 48:
        qos = "c_long"
        cmd += [ "--qos", qos ]
    if 8 < time <= 48:
        qos = "c_medium"
        cmd += [ "--qos", qos ]
    if maxiterations > 5:
        cmd += [ "--pty", "bash" ]
    cmd += [ runner ]
    print ( f"updater: {' '.join(cmd)}" )
    if dry_run:
        return
    subprocess.run ( cmd )

def clean_dirs( rundir, clean_all = False, verbose=True ):
    cmd = "rm slurm*out"
    o = subprocess.getoutput ( cmd )
    cmd = f"cd {rundir}; rm -rf old*hi .*slha H*hi ssm*pcl *old *png decays* states.dict hiscore.hi hiscore.cache Kold.conf Zold.conf RUN* xsec* llhdscanner*sh walker*log $OUTPUTS"
    if clean_all:
        cmd = f"cd {rundir}; rm -rf old*pcl H*hi hiscores.cache .cur* .old* .tri* .*slha M*png history.txt pmodel-*py pmodel.py llhd*png decays* RUN*.sh ruler* rawnumb* *tex hiscore.log hiscore.slha *html *png *log RUN* walker*log training*gz Kold.conf Zold.conf xsec* llhdscanner*sh hiscores.dict Kold.conf Kmin.conf"
        cmd = f"cd {rundir}; rm -rf old*pcl scan*pcl H*hi hiscore*hi hiscore*cache .cur* .old* .tri* .*slha M*png history.txt pmodel-*py pmodel.py pmodel.dict pmodel-*.dict llhd*png decays* RUN*.sh ruler* rawnumb* *tex hiscore.log hiscore.slha *html *png *log RUN* walker*log training*gz Kold.conf Zold.conf xsec* llhdscanner*sh hiscores.dict Kold.conf Kmin.conf old_hiscore.hi log.txt run.dict llhd*pcl L*sh S*sh llhdPlotScript.py *old $OUTPUTS/walk-*.out"
    if verbose:
        print ( f"[slurm.py] {cmd}" )
    o = subprocess.getoutput ( cmd )

def queryStats ( maxsteps : int ):
    """ just give us the statistics """
    import running_stats
    running_stats.count_jobs()
    running_stats.running_stats()
    if maxsteps != None:
        for i in range(maxsteps):
            time.sleep(30.)
            print()
            running_stats.count_jobs()
            running_stats.running_stats()
            print()

def logCall ():
    fname = f"{os.environ['HOME']}/walker.log"
    f=open( fname,"at")
    args = ""
    for i in sys.argv:
        if " " in i or "," in i or "[" in i:
            i = f'"{i}"'
        args += f"{i} "
    f.write ( f'[slurm.py-{time.strftime("%H:%M:%S")}] {args.strip()}\n' )
    f.close()

def cancelAllRunners():
    o = subprocess.getoutput ( "slurm q | grep RUNNER" )
    lines = o.split("\n")
    cancelled = []
    for line in lines:
        if not "RUNNER" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        cmd = f"scancel {nr}"
        subprocess.getoutput ( cmd )
        cancelled.append ( nr )
    print ( f"[slurm_walk] cancelled {', '.join(cancelled)}" )

def getMaxJobId() -> int:
    """ get the highest job id """
    o = subprocess.getoutput ( "slurm q | grep RUNNER" )
    lines = o.split("\n")
    nmax = 0
    for line in lines:
        tokens = line.split()
        nr = int(tokens[0])
        if nr > nmax:
            nmax = nr
    return nmax

def getMinJobId() -> int:
    """ get the lowest job id """
    o = subprocess.getoutput ( "slurm q | grep RUNNER" )
    lines = o.split("\n")
    nmin = 1e99
    for line in lines:
        tokens = line.split()
        nr = int(tokens[0])
        if nr < nmin:
            nmin = nr
    return nmin

def cancelRangeOfRunners( jrange : str ):
    """ cancel only the jrange of runners 
    :param jrange: ranges of job ids given as string,
    e.g. 100-102, -98, 120-, 100
    """ 
    import re
    jrange = jrange.strip(" ")
    if re.search('[a-zA-Z]', jrange) is not None:
        from running_stats import cancelJobsByString
        return cancelJobsByString ( jrange )
    if not "-" in jrange: # single job
        cmd = f"scancel {jrange}"
        subprocess.getoutput ( cmd )
        print ( f"[slurm_walk] cancelled {jrange}" )
        return
    cancelled = []
    p1 = jrange.find("-")
    if p1 == len(jrange)-1: ## range is given as '<min>-'
        maxJobId = getMaxJobId()
        jrange += str(maxJobId)
        cancelRangeOfRunners( jrange )
        return
    if p1 == 0: ## range given as '-<max>'
        minJobId = getMinJobId()
        jrange = str(minJobId) + jrange
        cancelRangeOfRunners( jrange )
        return

    if 0 < p1 < len(jrange)-1:
        # full range given
        jmin,jmax = int ( jrange[:p1] ), int ( jrange[p1+1:] )
        for i in range(jmin,jmax+1):
            cmd = f"scancel {i}"
            subprocess.getoutput ( cmd )
            cancelled.append ( i )
        print ( f"[slurm_walk] cancelled {', '.join(map(str,cancelled))}" )
        return
    o = subprocess.getoutput ( "slurm q | grep RUNNER" )
    lines = o.split("\n")
    running = []
    for line in lines:
        if not "RUNNER" in line:
            continue
        tokens = line.split()
        nr = tokens[0]
        running.append ( int ( nr ) )
    # print ( "[slurm_walk] FIXME sth is wrong" )


def main():
    import argparse
    argparser = argparse.ArgumentParser(description="slurm-run a walker")
    argparser.add_argument ( '-q','--query',
            help='query status, dont actually run (use -M to query repeatedly)',
            action="store_true" )
    argparser.add_argument ( '-d','--dry_run', help='dry-run, dont actually call srun',
                             action="store_true" )
    argparser.add_argument ( '-k','--keep',
            help='keep the shell scripts that are being run, do not remove them afters',
            action="store_true" )
    argparser.add_argument ( '--cancel_all', help='cancel all runners',
            action="store_true" )
    argparser.add_argument ( '--cancel', help='cancel a certain range of runners, e.g "65461977-65461985"',
            type=str, default = None )
    argparser.add_argument ( '--do_srcombine',
            help='do also use combined results, SLs or pyhf', action="store_true" )
    argparser.add_argument ( '--test_param_space',
            help='test the parameter space by keeping constant K and TL', action="store_true" )
    argparser.add_argument ( '--run_mcmc',
            help='run mcmc walk without changing dimensions', action="store_true" )
    argparser.add_argument ( '-U','--updater', help='run the hiscore updater. if maxsteps is none, run separately, else append to last job',
                             action="store_true" )
    argparser.add_argument ( '--uploadTo', help='specify directoy under smodels.github.io/protomodels to upload to [latest]', type=str, default='latest' )
    argparser.add_argument ( '--record_history', help='turn on the history recorder',
                             action="store_true" )
    argparser.add_argument ( '-S', '--scan', nargs="?",
                    help='run the teststatScanner on pid [SCAN], -1 means dont run, 0 means run on all unfrozen particles in hiscore.',
                    type=str, default=-1 )
    argparser.add_argument ( '-M', '--maxsteps', nargs="?",
                    help='maximum number of steps in a walker, max number of iterations in the updater [None=1000]',
                    type=int, default=None )
    argparser.add_argument ( '--select', nargs="?",
                    help='filter analysis results, ("all", "em", "ul", "txnames:T1,T2", ... ["all"]',
                    type=str, default="all" )
    argparser.add_argument ( '--forbidden',
                    help="Dont touch the particle ids mentioned here, e.g. '1000023,1000024' [None]",
                    type=str, default="[]" )
    argparser.add_argument ( '--yvariable', nargs="?",
                    help='run the teststatScanner for ss multipliers (pid,yvariable), -1 means ignore and run for mass scans instead. 0 means scan over all unfrozen ssms of hiscore.',
                    type=str, default="-1" )
    argparser.add_argument ( '-L', '--llhdscan', nargs="?",
                    help="run the llhd scanner on <pid> / 1000022, -1 means dont run. 0 means run on all unfrozen pids of hiscore. can use names, e.g. 'Xt'",
                    type=str, default=-1 )
    argparser.add_argument ( '--clean', help='clean up files from old runs',
                             action="store_true" )
    argparser.add_argument ( '--clean_all', help='clean up *all* files from old runs',
                             action="store_true" )
    argparser.add_argument ( '--dont_wallpids', help='dont wall up the chargino',
                             action="store_true" )
    argparser.add_argument ( '--allscans', help='run all the scans: masses, llhds, and ssmses',
                             action="store_true" )
    argparser.add_argument ( '--rewrite', help='force rewrite of scan scripts',
                             action="store_true" )
    argparser.add_argument ( '-n', '--nmin', nargs='?', help='minimum worker id [1]',
                        type=int, default=1 )
    argparser.add_argument ( '--seed', nargs='?', help='the random seed. 0 means random. None means, do not set. [None]',
                        type=int, default=None )
    argparser.add_argument ( '-C', '--cheatcode', nargs='?', help='use a cheat model [no_cheat]',
                        type=str, default="no_cheat" )
    argparser.add_argument ( '-N', '--nmax', nargs='?',
                        help='maximum worker id. Zero means nmin + 1. [0]',
                        type=int, default=0 )
    argparser.add_argument ( '-t', '--time', nargs='?', help='time in hours [8]',
                        type=int, default=8 )
    argparser.add_argument ( '--repeat', nargs='?', help='submit <n> times [1]',
                        type=int, default=1 )
    argparser.add_argument ( '-p', '--nprocesses', nargs='?',
            help='number of processes to split task up to, 0 means one per worker [0]',
            type=int, default=0 )
    argparser.add_argument ( '-f', '--cont', help='continue with saved states (path to pickle file, or empty) [""]',
                        type=str, default="" )
    argparser.add_argument ( '-R', '--rundir',
                        help='override the default rundir. can use wildcards [None]',
                        type=str, default=None )
    argparser.add_argument ( '-T', '--templateSLHA',
                        help='path to template SLHA [template1g.slha]',
                        type=str, default=None )
    argparser.add_argument ( '--stopTeleportationAfter',
                        help='stop teleportation after this step [-1]',
                        type=int, default=-1 )
    argparser.add_argument ( '-D', '--dbpath', help='path to database, or "fake1" or "real" or "default" ["none"]',
                        type=str, default="default" )
    args=argparser.parse_args()
    args.yvariable = namer.pid ( args.yvariable )
    if args.yvariable == "-1":
        args.yvariable = -1
    if type(args.llhdscan) == str:
        if "X" in args.llhdscan:
            tmp = namer.pid ( args.llhdscan )
            if tmp == None:
                print ( f"[slurm_walk.py] error: cannot find pid for {args.llhdscan}" )
                sys.exit()
            else:
                args.llhdscan = tmp
        try:
            args.llhdscan = int ( args.llhdscan )
        except TypeError as e:
            print ( f"[slurm_walk.py] error: {e}" )
    if args.cancel:
        cancelRangeOfRunners ( args.cancel )
        return
    if args.cancel_all:
        cancelAllRunners()
        return
    mkdir ( outputdir, False )
    args.rewrite = True
    if args.nmax > 0 and args.dbpath == "none":
        print ( "dbpath not specified. not starting. note, you can use 'real' or 'fake1' as dbpath" )
        return
    rundir = defaultrundir
    if args.rundir != None:
        rundir = args.rundir
        if not "/" in rundir:
            rundir = f"{basedir}/{rundir}/"

    rundirs = glob.glob ( rundir )
    if rundirs == []:
        # rundirs = [ "./" ]
        rundirs = [ rundir ]
    rundirs.sort()
    if len(rundirs)>1:
        print ( f"[slurm.py] rundirs {YELLOW} {', '.join(rundirs)}{RESET}" )
    else:
        print ( f"[slurm.py] rundir {YELLOW} {rundirs[0]}{RESET}" )

    if not args.query:
        logCall ()

    totjobs = 0

    for rd,rundir in enumerate(rundirs):
        mkdir ( rundir )
        seed = args.seed
        if seed != None and seed > 0 and rd>0:
            seed += (len(nprocesses)+1)*rd
        if seed == 0:
            seed = int ( random.uniform ( 10**6, 10**8 ) )
        if seed != None and type(seed)==int and seed>2**31-1:
            seed = seed % 1073741823

        time.sleep ( random.uniform ( .004, .009 ) )
        dbpath = args.dbpath
        if dbpath == "real":
            dbpath = f"{codedir}/smodels-database"
        if args.dbpath == "default": ## make sure we always set from scratch
            # dbpath = rundir + "/default.pcl"
            dbpath = "official"
        if "fake" in dbpath and not dbpath.endswith(".pcl"):
            dbpath = f"{dbpath}.pcl"

        if args.allscans:
            subprocess.getoutput ( f"./slurm.py -R {rundir} -S 0" )
            subprocess.getoutput ( f"./slurm.py -R {rundir} -S 0 --yvariable 0" )
            subprocess.getoutput ( f"./slurm.py -R {rundir} -L 0" )
            continue

        if args.query:
            queryStats ( args.maxsteps )
            continue
        if args.clean:
            clean_dirs( rundir, clean_all = False )
            continue
        if args.clean_all:
            clean_dirs( rundir, clean_all = True )
            continue
        if args.scan != -1:
            rewrite = True # args.rewrite
            for i in range(args.repeat):
                runScanner ( args.scan, args.dry_run, args.time, rewrite, args.yvariable, rundir, dbpath, args.select, args.do_srcombine, args.uploadTo )
            continue
        if args.llhdscan != -1:
            for i in range(args.repeat):
                runLLHDScanner ( args.llhdscan, args.yvariable, args.dry_run, args.time, args.rewrite, rundir, args.select, args.do_srcombine, args.uploadTo )
            continue

        #with open("run_walker.sh","rt") as f:
        #    lines=f.readlines()
        nmin, nmax, cont = args.nmin, args.nmax, args.cont
        cheatcode = args.cheatcode
        if nmax == 0 or nmax < nmin:
            nmax = nmin
        nworkers = nmax - nmin + 1
        nprocesses = min ( args.nprocesses, nworkers )
        if nprocesses == 0:
            nprocesses = nworkers

        restartctr = 0
        update_hiscores = args.updater ## False
        if args.stopTeleportationAfter == None:
            args.stopTeleportationAfter = -1
        if args.maxsteps == None:
            args.maxsteps = 1000
        wallpids = not args.dont_wallpids
        while True:
            if nprocesses == 1:
                for i in range(args.repeat):
                    runOneJob ( 0, nmin, nmax, cont, dbpath, args.dry_run,
                      args.keep, args.time, cheatcode, rundir, args.maxsteps,
                      args.select, args.do_srcombine, args.record_history, args.test_param_space, args.run_mcmc, seed,
                      update_hiscores, args.stopTeleportationAfter, args.forbidden,
                      wallpids, args.templateSLHA )
                totjobs+=1
            else:
                import multiprocessing
                ## nwalkers is the number of jobs per process
                nwalkers = 0
                if nprocesses > 0:
                    nwalkers = int ( math.ceil ( nworkers / nprocesses ) )
                jobs = []
                for i in range(nprocesses):
                    update_hiscores = False
                    if args.updater and i == nprocesses-1:
                        update_hiscores = True
                    imin = nmin + i*nwalkers
                    imax = imin + nwalkers
                    if seed != None: ## we count up
                        seed += (1+len(rundirs))*(1+nprocesses)
                    p = multiprocessing.Process ( target = runOneJob,
                        args = ( i, imin, imax, cont, dbpath, args.dry_run,
                        args.keep, args.time, cheatcode, rundir, args.maxsteps,
                        args.select, args.do_srcombine, args.record_history, args.test_param_space, args.run_mcmc, seed,
                        update_hiscores, args.stopTeleportationAfter, args.forbidden,
                        wallpids, args.templateSLHA ) )
                    jobs.append ( p )
                    p.start()
                    time.sleep ( random.uniform ( 0.006, .01 ) )

                for j in jobs:
                    j.join()
                res = RESET
                col = GREEN
                totjobs+=len(jobs)
                if len(jobs) in [ 48, 49, 51 ]:
                    colo = RED
                if len(jobs)>0:
                    print ( f"{col}[slurm.py] collected {len(jobs)} jobs.{res}" )
            break
        res = RESET
        col = GREEN
        if totjobs % 10 != 0 and (totjobs)>1:
            col = RED
        if totjobs == 0:
            col = RED
        if args.updater:
            ## update flag given standalone
            #maxsteps = args.maxsteps
            #if maxsteps == None:
            #    maxsteps = 1
            #    for i in range(args.repeat):
            runUpdater( args.dry_run, args.time, rundir, 1,
                    dbpath = dbpath, uploadTo = args.uploadTo )
            totjobs += 1
            #    continue
        print ( f"{col}[slurm.py] In total we submitted {totjobs} jobs.{res}" )
        if seed != None: ## count up
            seed += (1+len(rundirs))*(1+nprocesses)

if __name__ == "__main__":
    main()

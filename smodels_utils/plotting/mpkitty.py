""" a bit of code to try to import the matplotlib-kitty backend,
    if that fails then fall back to ordinary matplotlib """

options = { "hasKittyBackend": False }

def importBackend():
    import os
    if "jupyter" in os.environ["_"]:
        return
    try:
        import matplotlib, os, sys, subprocess
        from smodels_utils import SModelSUtils
        home = os.environ["HOME"]
        info = sys.version_info
        ver = f"{info.major}.{info.minor}"
        path = f"{home}/.local/lib/python{ver}/site-packages/"
        name = "matplotlib-backend-kitty"
        filename = os.path.join ( path, name )
        if not os.path.exists ( filename ):
            cmd = f"mkdir -p {path}"
            subprocess.getoutput ( cmd )
            sourcedir = os.path.join ( SModelSUtils.installDirectory(), "smodels_utils", "plotting" )
            cmd = f"cp -r {sourcedir}/{name} {path}"
            o = subprocess.getoutput ( cmd )

        try:
            matplotlib.use('module://matplotlib-backend-kitty')
            options["hasKittyBackend"] = True
        except (ModuleNotFoundError,ImportError) as e:
            options["hasKittyBackend"] = False

    except Exception as e:
        pass

importBackend()
import matplotlib.pyplot as plt
from matplotlib.pyplot import *

def timg( filename ):
    """ use timg to show filename in the terminal """
    import os
    if not options["hasKittyBackend"] and not "kitty" in os.environ["TERM"]:
        return
    from shutil import which
    exe = which ("timg", path=f"{os.environ['HOME']}/.local/bin:/usr/bin:{os.environ['PATH']}" )
    if exe is None:
        return
    import subprocess
    ver = subprocess.getoutput ( f"{exe} --version" )
    ver = ver.replace("timg ","")
    ver = ver.strip()
    cols = "120"
    if "MPLBACKEND_KITTY_SIZING" in os.environ:
        cols = os.environ["MPLBACKEND_KITTY_SIZING"]
    cmd = f"{exe} -pkitty -g {cols}x80 -U -W {filename}"
    if "users" in exe:
        cmd = f"{exe} {filename}"
    if ver.startswith ( "1.1" ):
        cmd = f"{exe} -s 80 -c extended {filename}"

    print () # make sure we start in a fresh line
    o = subprocess.getoutput ( cmd )
    # print ( f"[mpkitty] {o}" )
    print ( o )
            
def kittyPlot( filename = None, show = True ):
    """ save to filename, possibly also show in terminal
    :param show: if True, then also print to terminal
    """
    deleteIt = False
    if filename == None:
        import tempfile
        filename = tempfile.mktemp(suffix=".png")
        # plt.show() should actually work, but doesnt right now
        # return # for now
        deleteIt = True
    plt.savefig ( filename )
    if show:
        timg ( filename )
    import os
    if deleteIt and os.path.exists ( filename ):
        os.unlink ( filename )


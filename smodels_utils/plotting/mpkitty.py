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

        matplotlib.use('module://matplotlib-backend-kitty')
        options["hasKittyBackend"] = True

    except Exception as e:
        pass

importBackend()
import matplotlib.pyplot as plt
def kittyPlot( filename = None ):
    if filename == None:
        # plt.show() should actually work, but doesnt right now
        return # for now
    plt.savefig ( filename )
    import os
    if options["hasKittyBackend"] == True or "kitty" in os.environ["TERM"]:
        cols = "120"
        if "MPLBACKEND_KITTY_SIZING" in os.environ:
            cols = os.environ["MPLBACKEND_KITTY_SIZING"]
        cmd = f"timg -pkitty -g {cols}x80 -U -W {filename}"
        import subprocess
        o = subprocess.getoutput ( cmd )
            
from matplotlib.pyplot import *

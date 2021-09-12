""" a bit of code to try to import the matplotlib-kitty backend,
    if that fails then fall back to ordinary matplotlib """

def importBackend():
    try:
        import matplotlib, os, sys, subprocess
        from smodels_utils import SModelSUtils
        home = os.environ["HOME"]
        ver = sys.version[:3]
        path = f"{home}/.local/lib/python{ver}/site-packages/"
        name = "matplotlib-backend-kitty"
        if not os.path.exists ( os.path.join ( path, name ) ):
            cmd = f"mkdir -p {path}"
            subprocess.getoutput ( cmd )
            sourcedir = os.path.join ( SModelSUtils.installDirectory(), "smodels_utils", "plotting" )
            cmd = f"cp -r {sourcedir}/{name} {path}"
            o = subprocess.getoutput ( cmd )

    matplotlib.use('module://matplotlib-backend-kitty')

    except Exception as e:
        pass

importBackend()
import matplotlib.pyplot as plt
from matplotlib.pyplot import *

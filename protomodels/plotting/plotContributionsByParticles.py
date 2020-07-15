#!/usr/bin/env python3

import roughviz
import pandas as pd 
import subprocess

d = {'Contribution': ['$\\tilde{g}$', '$t_{2}$', '~t1', 'b<sub>1</sub>', 'C1' ], 'p': [.52, .20, .17, .07, .04] }
df = pd.DataFrame(data=d )

roughviz.pie(df["Contribution"], df["p"], plot_svg=False, interactive=False, legend=False, axisRoughness = 0.7, axisStrokeWidth = 0.7, roughness=2.3, highlight="gray" )

cmd = "wkhtmltoimage output.html output.svg"
subprocess.getoutput ( cmd )
print ( "eog output.svg" )

#!/usr/bin/env python3

import glob, subprocess

def main():
    cmd = "tar xzvf T6Gamma.tar.gz"
    subprocess.getoutput ( cmd )
    files = glob.glob("T6Gamma*slha" )
    for fl in files:
        print ( "fixing", fl )
        with open ( fl, "rt" ) as f:
            lines = f.readlines()
        with open ( fl, "wt" ) as f:
            for line in lines:
                f.write ( line )
                if "1000012" in line:
                    f.write ( "   2000012     1.00000000E+05   # ~nu_eR\n" )
                    f.write ( "   2000014     1.00000000E+05   # ~nu_muR\n" )
                    f.write ( "   2000016     1.00000000E+05   # ~nu_tauR\n" )
                    f.write ( "   1000045     1.00000000E+05   # ~chi_50\n" )
                    f.write ( "   45     1.00000000E+05   # ? \n" )
                    f.write ( "   46     1.00000000E+05   # ? \n" )
    cmd = "tar czvf T6Gamma.tar.gz T6Gamma*slha" 
    subprocess.getoutput ( cmd )

main()

import argparse
import os, sys

def getParserArgs():
    """ get the parser args, but also set all env vars,
        and sys paths 
    :returns: parser args
    """
    argparser = argparse.ArgumentParser(description =
        'create info.txt, txname.txt, and sms.root')
    argparser.add_argument ('-utilsPath', '--utilsPath',
        help = 'path to the package smodels_utils',\
        type = str, default = os.path.expanduser('~/smodels-utils') )
    argparser.add_argument ('-smodelsPath', '--smodelsPath',
        help = 'path to the package smodels_utils',\
        type = str, default = os.path.expanduser('~/smodels') )
    argparser.add_argument ('-no', '--noUpdate',
        help = 'do not update the lastUpdate field.',\
        action= "store_true" )
    argparser.add_argument ('-r', '--resetValidation',
        help = 'reset the validation flag',\
        action= "store_true" )

    args = argparser.parse_args()

    if args.noUpdate:
        os.environ["SMODELS_NOUPDATE"]="1"

    if args.resetValidation:
        os.environ["SMODELS_RESETVALIDATION"]="1"

    if args.utilsPath:
        utilsPath = args.utilsPath
    else:
        databaseRoot = '../../../'
        sys.path.append(os.path.abspath(databaseRoot))
        from utilsPath import utilsPath
        utilsPath = databaseRoot + utilsPath
    if args.smodelsPath:
        sys.path.append(os.path.abspath(args.smodelsPath))

    sys.path.append(os.path.abspath(utilsPath))
        
    return args

#!/usr/bin/python

import convertHelpers

for expid in [ 
    "ATLAS_CONF_2013_024",
    "ATLAS_CONF_2013_035",  
    "ATLAS_CONF_2013_037",
    "ATLAS_CONF_2013_047",
    "ATLAS_CONF_2013_048",  
    "ATLAS_CONF_2013_049", 
    "ATLAS_CONF_2013_053",  
    "ATLAS_CONF_2013_054",  
    "ATLAS_CONF_2013_061",
    "ATLAS_CONF_2013_062",
    "ATLAS_CONF_2013_093" 
        ]:

    convertHelpers.createInfoFile ( expid )
    for cut in range(15):
        has_globals=False
        for ana in range(15):
            if convertHelpers.existsAnalysisCut ( expid, ana, cut ):
                convertHelpers.copyEffiFiles ( expid, ana, cut )
                convertHelpers.createAndRunConvertFiles ( expid, cut, dry_run=True )
                if not has_globals:
                    convertHelpers.createDataInfoFile ( expid, cut )
                    convertHelpers.copyValidationScripts ( expid )
                    has_globals=True

    convertHelpers.mergeSmsRootFiles ( expid )
#            else:
#                print "expid,ana,cut",expid,ana,cut,"doesnt exist?"

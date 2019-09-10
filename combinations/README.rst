This folder is all about combining different analyses, and finding the best
combination. Including the artificial model builder.

Random walker
^^^^^^^^^^^^^

  * Randomly builds models and compares them against the SMS results
  * Try: ./walker.py -h

Regressor
^^^^^^^^^

  * Called from the command line, can be used to train the Z score prediction network
  * Try: ./regressor.py -h

Hiscore
^^^^^^^
  * The hiscore.py script can be used to collect the hiscores from the different walkers, 
    trim them, compute analysis contributions.  
  * Try: ./hiscore.py -h
  * Use plotHiscore.py to produce web pages like http://www.hephy.at/user/wwaltenberger/models/

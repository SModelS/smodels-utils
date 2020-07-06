# ProtoModel



## Refactoring history:


  * Files and code related to the ML (accelerator.py, history.py, RandomWalker.train/gradiantAscent, ...) have been removed at commit 2df10f232ff52168
  * remove model from folder names
  * mv hiscore.py to modelWalker
  * mv expResModifier.py to tools
  * removed resolveMuhat from takeStep (I've checked and it was useless)
  * move protomodel.backup, clean, and restore to manipulator (renamed to backupModel, restoreModel, delBackup, cleanBestCombo)
  * renamed Manipulator.resolveMuhat to Manipulator.rescaleByMuHat
  * moved computeParticleContributions and computeAnalysisContributions to hiscore.py. Tried to simplify  computeParticleContributions
  * added predictor to Hiscore.predictor (so it can recompute stuff)
  * renamed runWalk.py -> walk.py
  * split hiscore code into: Hiscore class (builder/hiscore.py) and hiscore tools (tools/hiscoreTools.py)
  * added loadHiscores.py
  * make sure protomodel always has at least 2 particles
  * remove swap particles. Canonical ordering is enforced when changing the model (change in behavior: when removing the particles not present in the best combination, the lighter state is no longer removed if the heavier state appears in the combination. Before the lighter state was removed and the heavy state was then swapped.)
  * if the LSP mass is changed, make sure it is only allowed to change up to the next-to-lightest state (change in behavior: before all the masses smaller than the LSP were change to LSP mass + 1)
  * added a copy method in Protomodel to allow for a cheaper (deep) copy of the object
  * changes in model merger:
    * Now ther merger is always performed (before it was random) and all good candidates are merged
    * The merger function was partially rewritten (it seems there was a bug before where only one sign of the PID to be replaced was looked for and a single decay {PID : BR} was being replaced by {PIDA,PIDB) : BR} -> Check!)
    * The predictions are computed for the merged protomodel in RandomWalker.onestep (before it was inside Manipulator.merge)
    * If the merged model has higher Z, it replaces the original protomodel (before the xsecs were rescaled by 1/rmax, but I don't think this is necessary, since, for computing Z, mu is a free parameter)

## Refactoring ToDo:

  * FIX computeNewSSMs (called by merge particles). It requires stored_xsecs, but when were these stored before?
  * simplify computeParticleContributions (?)
  * replace xsecComputer with an interpolation based on the pMSSM scan (?)


## Profiling:

  * onestep (98%)
    * predictor.predict (55%)
      * computeSignificance (57%)
        * combiner.computePrior (85%)      
        * combiner.findHighestSignificance (15%)
      * updateModelPredictions (22%)
      * runSModelS (21%)
    * manipulator.randomlyChangeModel (34%)
      * protomodel.createSLHAFile (93%)
      * randomlyChangeMasses (7%)
    * manipulator.checkSwaps (11%)
  * decideOnTakingStep (2%)

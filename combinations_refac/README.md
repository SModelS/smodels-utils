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

## Refactoring ToDo:


  * simplify swap particles (move it to the end of Manipulator.randomlyChangeModel)
  * simplify merge particles (?)
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

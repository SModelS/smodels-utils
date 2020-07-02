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


## Refactoring ToDo:

  * split hiscore code into: Hiscore class (held by RandomWalker) and hiscore methods to consolidate the results
  * simplify swap particles (move it to the end of Manipulator.randomlyChangeModel)
  * simplify merge particles (?)
  * simplify computeParticleContributions (?)



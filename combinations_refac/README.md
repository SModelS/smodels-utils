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
    * Added getXsecs(), _stored_xsecs, _xsecMasses and _xsecSSMs to ProtoModel. Now all access to the cross-sections should be through ProtoModel.getXsecs()
    * ProtoModel.computeXSecs now automatically stores the xsecs, masses and SSMs used in the ProtoModel attributes.
    * Now RandomWalker keeps track of current (old) K and Z values (instead of ProtoModel)
    * Rewrote how branching ratios are modified.
      * Added ProtoModel.getOpenChannels to find which decay channels are (kinematically) allowed (uses ProtoModel.possibledecays)
      * All decays are created from ProtoModel.possibledecays, so ProtoModel.decays does not have to contain closed decay channels or channels with zero BR
      * Added Manipulator.setRandomBranchings (to assign random BRs when unfreezing particles)
      * Modified Manipulator.normalizeBranchings (now it only normalizes the BRs, so the total is 1)
      * Modified Manipulator.removeAllOffshell (now it removed all kinematically forbidden/frozen channels and rescale BRs)
      * Changed a bit the behavior of randomlyChangeBranchingOfPid (how random changes are made). All new decays are created using ProtoModel.getOpenChannels
    * Rewrote how signal strength multipliers are merged (replaced computeNewSSMs by mergeSSMs)
    * Added __str__ and __repr__ methods to ProtoModel
    * Manipulator.freezePidsNotInBestCombo always keeps at least 2 particles (LSP + 1)
    * If no combination was found, the Z and K values are set to None and the step is reverted
    * Moved cross-section calculation methods to ProtoModel (now the cross-sections calculation and SLHA creation are independent steps)
    * Removed protoxsecs.py
    * Only information about unfrozen particles is kept in Protomodel.decays, Protomodel.masses and Protomodel.ssmultipliers (so total number of particles is given by ProtoModel.particles)
    * Frozen particles are no longer assigned decoupled masses (except when writing to the SLHA file)
    * Changed resolveMuHat->rescaleBy->rescaleSignalBy. The rescaling now also takes care of the signal values in ProtoModel.tpList, ProtoModel.bestCombo and _stored_xsecs
    * Added ProtoModel.rescaleXSecsBy to rescale the cross-sections stored in _stored_xsecs and the signal strength multipliers
    * Small refactoring of ProtoModel.initializeModel
    * Small refactoring of Hiscore.computeParticleContributions
    * freezePidsNotInBestCombo has been moved to the beginning of each step (the model is no longer trimmed at the end of each step)
    * Moved part of Manipulator.randomlyUnfreezeParticle to Manipulator.unFreezeParticle
    * Added basic unit tests
    * Moved _run and startWalkers from randomWalker.py to walkingWorker.py
    * Added Combiner object to Predictor.combiner

## Refactoring ToDo:

  * minimize deepcopies
  * replace xsecComputer with an interpolation based on the pMSSM scan (?)
  * change hiscore pickle file extension (to .hi?)



## Refactoring Behavior Changes
  * Set random BRs and ssmmultipliers to 1.0 when unfreezing particle (no previous information is used)
  * Cross-sections are no longer kept in the SLHA file.

## Profiling:

Fraction of time spent in each main method (running 300 steps with 10k events for xsec calculation):

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

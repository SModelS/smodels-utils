#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: main.py
   :synopsis: front end of training new neural networks
.. moduleauthor:: Philipp Neuhuber <ph.neuhuber@gmail.com>

"""

import argparse
from parameter import Parameter
from system.dataset import DatasetBuilder, Data #set
from system.modelTrainer import ModelTrainer
from system.initnet import DatabaseNetwork

def main(parameter):

	"""
	Example usage of neural network training methods.
	Reads the parameter file and trains networks for all
	maps it can find.

	:param parameter: Custom parameter dictionary

	:return x: Coordinate value (float)

	"""

	# ----------------------------------------------------------------------------------- #
	# custom dictionary class that automatically permutates all possible map combinations #
	# ----------------------------------------------------------------------------------- #

	thingsToTrain = parameter["database"]

	# -------------------------------------------------------------------------------- #
	# loop over all analysis map combinations of the parameter file [database] section #
	# -------------------------------------------------------------------------------- #

	while(thingsToTrain.incrIndex):

		# ----------------------------------------------- #
		# load experimental data of current configuration #
		# ----------------------------------------------- #

		parameter.loadExpres

		# -------------------------------------------------------------- #
		# load custom class that will generate our datasets for training #
		# -------------------------------------------------------------- #

		builder = DatasetBuilder(parameter)

		# -------------------------------------------------------------------------------------- #
		# add optional reference xsec cut if efficiencies get too small.						 #
		# training of unneccessarily small effs undermines the performance of the whole network. #
		# cutoff formula: lumi * eff * refxsec(m0) > 1e-2										 #
		# -------------------------------------------------------------------------------------- #

		#builder.addrefXsecCut() #"filename", columns = {..}

		# --------------------------------------------------------------- #
		# optional filter condition for loaded or generated datasets. NYI #			
		# --------------------------------------------------------------- #

		#builder.addFilterCondition(column, condition) eg bigwidths filter, or only every x-th datapoint accepted

		# ---------------------------------------------------------------------------- #
		# train both model types separately, combine them afterwards into one ensemble #
		# ---------------------------------------------------------------------------- #

		winner = {}
		for nettype in ["regression","classification"]:
			parameter.set("nettype", nettype)

			# ------------------------------------------------- #
			# generate or load dataset used for training 		#
			# output will be custom Dataset class used by torch #
			# ------------------------------------------------- #

			dataset = builder.run(nettype)

			# ------------------------------------------------------- #
			# initializing trainer class for current map and net type #
			# ------------------------------------------------------- #

			trainer = ModelTrainer(parameter, dataset)

			# --------------------------------------------------------------------------------------- #
			# running trainer on all hyperparam configurations and saving the best performing network #
			# --------------------------------------------------------------------------------------- #

			winner[nettype] = trainer.run()
		
		# -------------------------------------------------------------------------------------------- #
		# combining best performing regression and classification networks into final ensemble network #
		# -------------------------------------------------------------------------------------------- #

		ensemble = DatabaseNetwork(winner)
		ensemble.save(parameter["expres"], parameter["txNameData"])



if __name__=='__main__':

	ap = argparse.ArgumentParser(description="Trains and finds best performing neural networks for database analyses via hyperparameter search")
	ap.add_argument('-p', '--parfile', 
			help='parameter file', default='nn_parameters.ini')
	ap.add_argument('-l', '--log', 
			help='specifying the level of verbosity (error, warning, info, debug)',
			default = 'info', type = str)
	args = ap.parse_args()

	parameter = Parameter(args.parfile, args.log)

	main(parameter)


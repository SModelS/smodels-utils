#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys, torch, argparse
from system.initnet import *
from system.getTimings import *


def getOutputColumnWidth(expres):

	txnames = []
	for e in expres:
		for dataset in e.datasets:
			for txname in dataset.txnameList:
				tx = txname.txName
				if not tx in txnames:
					txnames.append(tx)

	return max(len(txname) for txname in txnames) + 2


def listInterpolTimes(db, analyses, txNames, dataselector, superseded = True, nonValidated = True):

	dataselector = "upperLimit"
	expres = db.getExpResults(analysisIDs = analyses, txnames = txNames, dataTypes = dataselector, useSuperseded = superseded, useNonValidated = nonValidated)
	colLen = getOutputColumnWidth(expres)

	print("\n  ---\n  INTERPOLATION TIMES:\n  ---")

	for e in expres:

		if e.id() == "ATLAS-SUSY-2016-07":
			continue
		if e.id() == "ATLAS-SUSY-2018-16":
			continue
		if e.id() == "ATLAS-SUSY-2018-31":
			continue
		if e.id() == "CMS-SUS-17-005":
			continue
		if e.id() == "CMS-SUS-17-006":
			continue

		print("\n  " + e.id() + ":")

		txnames = []
		for dataset in e.datasets:
			for txname in dataset.txnameList:
				tx = txname.txName
				if not tx in txnames:
					txnames.append(tx)

		if isinstance(txnames, list):

			for txname in txnames:

				mean, std = getInterpolTimeOnly(e, txname)
				print("  %s%s +- %sms" % (txname.ljust(colLen), str(round(mean, 3)), str(round(std, 3))))
				#print("  " + txname.ljust(colLen) + str(round(mean, 3)) + " +- " + str(round(std, 3)) + "ms")

				"""
				model = loadModel(e, txname)
				if model != None:
					lossReg = model.getValidationLoss("regression").item()
					lossCla = model.getValidationLoss("classification").item()
					speedFactor = 1. / model.getSpeedFactor()

					performance = str(round(lossReg, 3)) + " / " + str(round(lossCla, 3)) + " / " + str(round(speedFactor, 3))
				else: 
					performance = "N/A"
				"""
				

	print("\n  ---\n")


def listModels(db, analyses, txNames, dataselector, superseded = True, nonValidated = True):

	dataselector = "upperLimit"
	expres = db.getExpResults(analysisIDs = analyses, txnames = txNames, dataTypes = dataselector, useSuperseded = superseded, useNonValidated = nonValidated)
	colLen = getOutputColumnWidth(expres)

	targetDim = 3

	print("\n  SCANNING DATABASE:")
	print("  _________________________\n")
	print("  filtering for:")
	print("  type: %s, dim = %s" % (dataselector, targetDim))
	print("  _________________________\n")

	
	for e in expres:

		txnames, txs = [], []
		for dataset in e.datasets:
			for tx in dataset.txnameList:
				#tx = txname #.txName
				if not tx.txName in txnames:
					txnames.append(tx.txName)
					txs.append(tx)

		


		if isinstance(txs, list):

			for tx in txs:

				idPosted = False

				fullDim = tx.txnameData.full_dimensionality
				dim = tx.txnameData.dimensionality
				width = tx.txnameData.widthPosition

				if dim != targetDim: continue

				if not idPosted: 
					idPosted = True
					print("\n  " + e.id() + ":")

				model = loadModel(e, tx.txName)
				if model != None:
					lossReg = model.getValidationLoss("regression").item()
					lossCla = model.getValidationLoss("classification").item()
					speedFactor = 1. / model.getSpeedFactor()

					performance = "%s / %s / %s" % (str(round(lossReg, 3)), str(round(lossCla, 3)), str(round(speedFactor, 3)))
					#performance = str(round(lossReg, 3)) + " / " + str(round(lossCla, 3)) + " / " + str(round(speedFactor, 3))
				else: 
					performance = "N/A"

				print("  " + tx.txName.ljust(colLen) + performance)


	print("\n  ---\n")
	return

	dbPath = expres.path
	for i in range(len(dbPath)):
		if dbPath[i:i+8] == 'database':
			dbPath = dbPath[i:]
			break
	savePath = os.getcwd() + "/" + dbPath + "/models/"
	# ---

	fileName = txName + '.pth'


if __name__=='__main__':

	ap = argparse.ArgumentParser(description="Scans database for available neural networks and their performances")		 
	ap.add_argument('-l', '--listAll', help='list all available maps', action='store_true')
	ap.add_argument('-i', '--interpolTimes', help='list interpolation times of database maps', action='store_true')
	args = ap.parse_args()

	smodelsPath = "../../smodels"
	databasePath = "../../smodels-database"
	sys.path.append(smodelsPath)
	sys.path.append(databasePath)
	from smodels.experiment.databaseObj import Database

	db = Database(databasePath)

	if args.listAll:
		listModels(db, "all", "all", None)
	elif args.interpolTimes:
		listInterpolTimes(db, "all", "all", None)

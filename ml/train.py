#!/usr/bin/python3

import os
os.environ["KERAS_BACKEND"] = "tensorflow"
import numpy as np

from keras.models import Sequential
from keras.layers import Dense
from keras import callbacks
import time

## define the network
model = Sequential()
model.add(Dense(2, activation="relu", input_dim=2))
model.add(Dense(1, kernel_initializer="normal" )) ## activation="sigmoid"))
model.summary()

model.compile ( loss="mean_squared_error", optimizer="adam", metrics=["accuracy"] )
# model.compile ( loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"] )

print ( "Now loading database" )
from smodels.experiment.databaseObj import Database
database=Database("database/")
from smodels.tools.physicsUnits import GeV, fb

expres = database.getExpResults( analysisIDs=["CMS-PAS-SUS-12-026"] )[0]

print ( "Done loading database" )

data, labels = [], []

print ( "Now get upper limits" )
for mother in np.arange ( 0., 3000., 20. ):
    for lsp in np.arange ( 0., mother, 20. ):
        masses=[[ mother*GeV, lsp*GeV], [ mother*GeV, lsp*GeV] ]
        ul = expres.getUpperLimitFor ( txname="T1tttt", mass=masses )
        if type(ul) == type(None):
            continue
        data.append ( [ mother, lsp ] )
        labels.append ( ul.asNumber(fb) )
print ( "Done getting upper limits" )

cbk=callbacks.TensorBoard ( "logs/log_test_"+str(time.time()) )
cbk.set_model ( model )
            
print ( "Now fitting ... " )
history=model.fit ( np.array(data[::2]), np.array(labels[::2]), \
                    validation_data = ( np.array(data[1::2]), np.array(labels[1::2]) ), batch_size=len(data[::2]), epochs=100,
                    callbacks = [ cbk ] )
model.save("first.h5")

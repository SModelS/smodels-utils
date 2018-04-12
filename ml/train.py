#!/usr/bin/python3

import os
os.environ["KERAS_BACKEND"] = "tensorflow"
import numpy as np

from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Input
from keras import callbacks
import time
import IPython

#inputs = Input(shape=(1,))
#preds = Dense(1,activation='linear')(inputs)
#model = Model ( inputs=inputs, outputs=preds )
## define the network
model = Sequential()
model.add(Dense(2, activation="linear", input_shape=(2,)))
#model.add(Dense(12, init='uniform', activation='sigmoid'))
#model.add(Dense(12, init='uniform', activation='sigmoid'))
##model.add(Dense(1, kernel_initializer="normal" )) ## activation="sigmoid"))
#model.add(Activation('tanh'))
model.add(Dense(1,activation='sigmoid'))
model.summary()

model.compile ( loss="mean_squared_error", optimizer="adam", metrics=["mse"] )
# model.compile ( loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"] )

print ( "Now loading database" )
from smodels.experiment.databaseObj import Database
database=Database("database/")
from smodels.tools.physicsUnits import GeV, fb

expres = database.getExpResults( analysisIDs=["CMS-PAS-SUS-12-026"] )[0]

print ( "Done loading database" )

tr_data, tr_labels = [], []
val_data, val_labels=[], []

print ( "Now get upper limits" )
for mother in np.arange ( 600., 1100., 10. ):
    for lsp in np.arange ( 0., mother, 10. ):
        masses=[[ mother*GeV, lsp*GeV], [ mother*GeV, lsp*GeV] ]
        ul = expres.getUpperLimitFor ( txname="T1tttt", mass=masses )
        if type(ul) == type(None):
            continue
        tr_data.append ( np.array( [ mother, lsp ] ) )
        # tr_data.append ( np.array( [ mother ] ) )
        tr_labels.append ( ul.asNumber(fb) )
        if mother == 700. and lsp==200.:
            print ( "training data", mother, lsp, ul.asNumber(fb) )
for mother in np.arange ( 610., 1110., 40. ):
    for lsp in np.arange ( 10., mother, 40. ):
        masses=[[ mother*GeV, lsp*GeV], [ mother*GeV, lsp*GeV] ]
        ul = expres.getUpperLimitFor ( txname="T1tttt", mass=masses )
        if type(ul) == type(None):
            continue
        # val_data.append ( np.array ( [ mother ] ) )
        val_data.append ( np.array ( [ mother, lsp ] ) )
        val_labels.append ( ul.asNumber(fb) )
print ( "Done getting upper limits" )

#cbk=callbacks.TensorBoard ( "logs/log_test_"+str(time.time()), histogram_freq=1, write_graph=True )
cbk=callbacks.TensorBoard ( "logs/log.me", histogram_freq=1, write_graph=True )
cbk.set_model ( model )
            
print ( "Now fitting ... " )
history=model.fit ( np.array(tr_data), np.array(tr_labels), \
                    validation_data = ( np.array(val_data), np.array(val_labels) ), 
                    batch_size=10, epochs=10, callbacks = [ cbk ] )
print ( "Done fitting" )
mother,lsp=700,200
mass = np.array( [ [ 700, 200 ], [ 600, 100 ] ] )
# mass = np.array( [ mother ] )
preds=model.predict ( mass )
print ( "Now predict" ) 
for m,p in zip ( mass,preds ):
    print ( "%s -> %s" % ( m,p) )

model.save("first.h5")
# IPython.embed()

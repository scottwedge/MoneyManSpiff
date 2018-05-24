"""
The Convolutional Neural Network for Money Man Spiff
Created with Keras, trained with Theano backend
Architecture:

Author: Parker Timmerman
"""

from keras.engine.topology import Input
from keras.engine.training import Model
from keras.layers import Dense, Conv3D, MaxPooling2D, LSTM, TimeDistributed
from keras.layers.core import Flatten
from keras.regularizers import l2
from keras.optimizers import Adam
from keras.utils import np_utils, plot_model
import keras.backend as K

import numpy as np
import pickle

class Network():
    """ Convolutional Neural Network """
    
    def __init__(self, model_file=None):
        self.l2_const = 1e-4                                        # Coefficient for l2 penalty
        self.create_network()
        self.setup_trainer()

        if model_file:                                              # If weights are provided, load the network with them
            network_weights = pickle.load(open(model_file, 'rb'))
            self.model.set_weights(network_weights)                 # The self.model variabe is created in create_network(...)

    def create_network(self):
        """ Create the CNN """

        """
        Input for the network is a 5-Dimensional Tensor
        We interpret market data as a "video" snapshot of a given market
        (Number of "Videos", Frames in each video, Width, Height, Layers of each frame)
        
        Each frame has the following layers
        1: High
        2: Low
        3: Open
        4: Close
        5: Volume               !
        6: Quote Volume         !
        7: Weighted Average     !
        (This part needs something thinking/seeing what is available from APIs)
        """

        # (channels, width, height, frames)
        input_x = network = Input((3, 6, 6, 48))

        k_s = (3,3,3)                     # Kernel Size

        ## Convolutional Layers
        network = Conv3D(filters = 32,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer = l2(self.l2_const))(network)
        network = Conv3D(filters = 64,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer = l2(self.l2_const))(network)
        network = Conv3D(filters = 64,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer = l2(self.l2_const))(network)
        network = Conv3D(filters = 128,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer = l2(self.l2_const))(network)
        network = Conv3D(filters = 128,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer = l2(self.l2_const))(network)

        ## LSTM Layers
        network = TimeDistributed(LSTM(units = 256,
                kernel_regularizer = l2(self.l2_const)))(network)
        network = LSTM(units = 256,
                kernel_regularizer = l2(self.l2_const))(network)

        ## Output
        self.network = Dense(units = 1,
                activation = 'linear')(network)

        self.model = Model(inputs = input_x, outputs = self.network)
        print(self.model.summary())
        #plot_model(self.model, to_file="model.png", show_shapes=True)

    def setup_trainer(self):
        """ Compile the network and setup for training """
        
        optimizer = Adam()
        loss = 'mean_squared_error'
        self.model.compile(optimizer  = optimizer, loss = loss, metrics = ['accuracy'])
        
        def train_step(videos, prices, learning_rate, epochs):
            K.set_value(self.model.optimizer.lr, learning_rate)
            self.model.fit(x = videos,
                    y = prices,
                    batch_size = len(videos),
                    epochs = epochs,
                    verbose = 1)
        self.train_step = train_step

    def get_weights(self):
        """ Returns the weights of the network """
        return self.model.get_weights()

    def save_model(self, file_name):
        w = self.get_weights()
        pickle.dump(w, open(file_name, 'wb'), protocol = 2)

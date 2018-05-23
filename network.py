"""
The Convolutional Neural Network for Money Man Spiff
Created with Keras, trained with Theano backend
Architecture:

Author: Parker Timmerman
"""

from keras.engine.topology import Input
from keras.engine.training import Model
from keras.layers import Dense, Conv3D, MaxPooling2D
from keras.layers.code import Flatten
from keras.regularizers import l2
from keras.optimizers import Adam
from keras.utils import np_utils
import keras.backend as K

import numpy as np
import pickle

class Network():
    """ Convolutional Neural Network """
    
    def __init__(self, model_file=None):
        self.l2_const = 1e-4                                        # Coefficient for l2 penalty
        self.create_network()
        self._loss_train_optimizer()

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

        input_x = network = Input((3, 6, 6, 48))

        k_s = (3,3)                     # Kernel Size

        # Convolutional Layers
        # Maybe make some layers TimeDistributed(Conv2D(...)) ?
        network = Conv3D(filters = 32,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu"
                kernel_regularizer=l2(self.l2_const))(network)
        network = Conv3D(filters = 64,
                kernel_size = k_s,
                padding = "same",
                data_format = "channels_first",
                activation = "relu"
                kernel_regularizer=l2(self.l2_const))(network)
        #network = Conv3D(filters = 64,
        #        padding = "same",
        #        data_format = "channels_first",
        #        activation = "relu",
        #        kernel_regularizer=l2(self.l2_const))(network)
        network = Conv3D(filters = 128,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer=l2(self.l2_const))(network)
        network = Conv3D(filters = 128,
                padding = "same",
                data_format = "channels_first",
                activation = "relu",
                kernel_regularizer=l2(self.l2_const))(network)

        ## LSTM Layers


